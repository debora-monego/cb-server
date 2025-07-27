from flask import (
    Blueprint, request, jsonify, current_app, 
    Response, stream_with_context, send_file, abort
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound
from app.models import Job, JobType, JobStatus
from app.models.user import User
from app.jobs.forms import BaseJobForm, MoleculeJobForm, FibrilJobForm
from app.jobs.tasks import process_molecule_job, process_fibril_job, modify_crosslinks_job
from app import db
from datetime import datetime
import os
import json
import time
import logging
import yaml
from pathlib import Path
import shutil
import pandas as pd
from app.jobs import bp

bp = Blueprint('jobs', __name__)
logger = logging.getLogger(__name__)

# === File Handling Utilities ===
def get_job_directory(job_id: int) -> str:
    """Get the directory path for a job's files."""
    base_dir = current_app.config['UPLOAD_FOLDER']
    return os.path.join(base_dir, f'job_{job_id}')

def save_uploaded_file(file, job_dir: str, allowed_extensions: set) -> str:
    """Save an uploaded file to the job directory."""
    if not file:
        raise ValueError("No file provided")
        
    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1].lower()
    
    if extension not in allowed_extensions:
        raise ValueError(f"File type {extension} not allowed. Allowed types: {allowed_extensions}")
    
    filepath = os.path.join(job_dir, filename)
    file.save(filepath)
    return filepath

def save_text_as_file(content: str, filename: str, job_dir: str) -> str:
    """Save text content as a file."""
    filepath = os.path.join(job_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

# === API Routes ===
@bp.route('/crosslinks-data', methods=['GET'])
@jwt_required()
def get_crosslinks_data():
    """Get the full crosslinks configuration data."""
    current_user_id = int(get_jwt_identity())  # Convert back to int
    
    logger.debug("=== Debug Info ===")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Current user ID: {current_user_id}")
    logger.debug("================")

    try:
        # Update path to match your folder structure
        csv_path = os.path.join('app', 'static', 'data', 'transformed_crosslink_data_all_combinations.csv')
        
        logger.debug(f"Looking for CSV at: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at path: {csv_path}")
            return jsonify({
                'status': 'error',
                'message': 'Crosslinks data file not found'
            }), 404
            
        df = pd.read_csv(csv_path)
        species_list = sorted(df['species'].unique().tolist())
        crosslinks_data = df.to_dict('records')
        
        response_data = {
            'status': 'success',
            'species': species_list,
            'crosslinks': crosslinks_data
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error loading crosslinks data: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/species/<species>/crosslinks', methods=['GET'])
@jwt_required()
def get_species_crosslinks(species):
    """Get crosslink configurations for a specific species."""
    current_user_id = get_jwt_identity()
    
    logger.debug("=== Debug Info ===")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Current user ID: {current_user_id}")
    logger.debug("================")

    try:
        csv_path = os.path.join(current_app.static_folder, 'data', 'transformed_crosslink_data_all_combinations.csv')
        df = pd.read_csv(csv_path)
        
        species_df = df[df['species'] == species]
        
        if species_df.empty:
            return jsonify({
                'status': 'error',
                'message': f'No data found for species: {species}'
            }), 404
        
        crosslinks_data = {
            'n_terminal': {},
            'c_terminal': {}
        }
        
        for terminal in ['N', 'C']:
            terminal_df = species_df[species_df['RES-terminal'] == f'LYS-{terminal}']
            types = terminal_df['type'].unique().tolist()
            
            crosslinks_data[f'{terminal.lower()}_terminal'] = {
                'types': types,
                'combinations': {
                    type_name: terminal_df[terminal_df['type'] == type_name].apply(
                        lambda row: {
                            'combination': row['combination'],
                            'residues': [
                                {'res': row['R1'], 'pos': row['P1']},
                                {'res': row['R2'], 'pos': row['P2']},
                                {'res': row['R3'], 'pos': row['P3']}
                            ]
                        }, axis=1
                    ).tolist()
                    for type_name in types
                }
            }
        
        return jsonify({
            'status': 'success',
            'species': species,
            'crosslinks': crosslinks_data
        })
    except FileNotFoundError:
        logger.error("Crosslinks data file not found")
        return jsonify({
            'status': 'error',
            'message': 'Crosslinks data file not found'
        }), 404
    except Exception as e:
        logger.error(f"Error loading species crosslinks: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# === Job Handlers ===
class JobHandler:
    """Base class for job type handlers."""
    
    def __init__(self, job: Job, job_dir: str):
        self.job = job
        self.job_dir = job_dir
        
    def process_submission(self, data: dict) -> dict:
        """Process job submission data and return parameters."""
        raise NotImplementedError
        
    def validate_submission(self, data: dict) -> None:
        """Validate submission data."""
        raise NotImplementedError

class MoleculeJobHandler(JobHandler):
    """Handler for molecule generation jobs."""
    
    def validate_submission(self, data: dict) -> None:
        if data['inputMethod'] not in ['species', 'custom']:
            raise ValueError("Invalid input method")
            
        if data['inputMethod'] == 'species':
            if not data.get('species'):
                raise ValueError("Species must be selected")
            
            if data.get('enableCrosslinks'):
                if data.get('nTerminalType') != 'NONE' and not data.get('nTerminalPosition'):
                    raise ValueError("N-terminal position is required when type is selected")
                if data.get('cTerminalType') != 'NONE' and not data.get('cTerminalPosition'):
                    raise ValueError("C-terminal position is required when type is selected")
                
        else:  # custom input
            for chain in ['chainA', 'chainB', 'chainC']:
                sequence = data.get(chain)
                if not sequence:
                    raise ValueError(f"{chain} sequence is required")
                if not isinstance(sequence, str):
                    raise ValueError(f"{chain} must be a string")
                if len(sequence) < 950 or len(sequence) > 1150:
                    raise ValueError(f"{chain} length must be between 950 and 1150")
                if not all(c in 'ABCDEFGHIKLMNOPQRSTUVWXYZ-' for c in sequence):
                    raise ValueError(f"{chain} contains invalid characters")
    
    def process_submission(self, data: dict) -> dict:
        """Process molecule job submission."""
        self.validate_submission(data)
        
        config = json.loads(data['config'])
        
        if data['inputMethod'] == 'custom':
            sequences = f">ChainA\n{data['chainA']}\n>ChainB\n{data['chainB']}\n>ChainC\n{data['chainC']}"
            fasta_path = save_text_as_file(
                sequences,
                'sequences.fasta',
                self.job_dir
            )
            config['fasta_file'] = fasta_path
            
        return config

# === Job Management Routes ===
@bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_job():
    """Handle job submission."""
    current_user_id = get_jwt_identity()
    
    try:
        job_type = request.json.get('job_type')
        if not job_type:
            return jsonify({'error': 'Job type not specified'}), 400
            
        job = Job(
            user_id=current_user_id,
            job_type=JobType(job_type),
            description=request.json.get('description', ''),
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.flush()
        
        job_dir = get_job_directory(job.id)
        os.makedirs(job_dir, exist_ok=True)
        
        try:
            handlers = {
                'molecule': MoleculeJobHandler,
            }
            
            handler_class = handlers.get(job_type)
            if not handler_class:
                raise ValueError(f"Unsupported job type: {job_type}")
                
            handler = handler_class(job, job_dir)
            job.parameters = handler.process_submission(request.json)
            
            task_map = {
                'molecule': process_molecule_job,
                'fibril': process_fibril_job,
            }
            
            task = task_map[job_type].delay(job.id)
            job.celery_task_id = task.id
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'job_id': job.id,
                'message': 'Job submitted successfully'
            })
            
        except Exception as e:
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)
            raise
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting job: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/', methods=['GET'])
@jwt_required()
def list_jobs():
    """List all jobs for the current user."""
    current_user_id = get_jwt_identity()
    
    try:
        jobs = Job.query.filter_by(user_id=current_user_id)\
                       .order_by(Job.created_at.desc())\
                       .all()
        
        return jsonify({
            'status': 'success',
            'jobs': [{
                'id': job.id,
                'type': job.job_type.value,
                'status': job.status.value,
                'created_at': job.created_at.isoformat(),
                'description': job.description
            } for job in jobs]
        })
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<int:job_id>', methods=['GET'])
@jwt_required()
def get_job(job_id):
    """Get details of a specific job."""
    current_user_id = get_jwt_identity()
    
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user_id:
        abort(403)
        
    return jsonify({
        'id': job.id,
        'type': job.job_type.value,
        'status': job.status.value,
        'progress': job.progress,
        'current_step': job.current_step,
        'error_message': job.error_message,
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'description': job.description,
        'parameters': job.parameters,
        'output_files': list(job.output_files.keys()) if job.output_files else [],
        'can_cancel': job.status in [JobStatus.QUEUED, JobStatus.RUNNING]
    })

@bp.route('/<int:job_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_job(job_id):
    """Cancel a running job."""
    current_user_id = get_jwt_identity()
    
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user_id:
        abort(403)
    
    if job.status not in [JobStatus.QUEUED, JobStatus.RUNNING]:
        return jsonify({'error': 'Job cannot be cancelled'}), 400
        
    try:
        if job.celery_task_id:
            from app import celery
            celery.control.revoke(job.celery_task_id, terminate=True)
        
        job.status = JobStatus.CANCELLED
        job.error_message = "Job cancelled by user"
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Job cancelled successfully'})
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:job_id>/files/<file_type>', methods=['GET'])
@jwt_required()
def download_file(job_id, file_type):
    """Download job output files."""
    current_user_id = get_jwt_identity()
    
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user_id:
        abort(403)
    
    if file_type not in job.output_files:
        abort(404)
        
    file_path = job.output_files[file_type]
    if not os.path.exists(file_path):
        abort(404)
        
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"job_{job_id}_{file_type}{os.path.splitext(file_path)[1]}"
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        abort(500)

@bp.route('/<int:job_id>/cleanup', methods=['POST'])
@jwt_required()
def cleanup_job(job_id):
    """Clean up job files."""
    current_user_id = get_jwt_identity()
    
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user_id:
        abort(403)
    
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        return jsonify({'error': 'Cannot clean up active job'}), 400
        
    try:
        job_dir = get_job_directory(job_id)
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)
            
        job.output_files = {}
        job.input_files = {}
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Job files cleaned up successfully'})
    except Exception as e:
        logger.error(f"Error cleaning up job: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500