# app/jobs/tasks.py

from celery import shared_task, Task
from celery.signals import task_failure, task_success, task_retry
from celery.utils.log import get_task_logger
from app.molecular.colbuilder import (
    generate_collagen_molecule,
    create_collagen_fibril,
    modify_crosslinks,
    change_density
)
from app.models import Job, JobStatus
from app import db
from datetime import datetime, timedelta
import traceback
import os
import shutil

logger = get_task_logger(__name__)

class BaseJobTask(Task):
    """Base task class with common functionality for all job tasks."""
    
    abstract = True
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        job_id = args[0] if args else None
        if job_id:
            job = Job.query.get(job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress = 100
                db.session.commit()
                logger.info(f"Task {task_id} completed successfully for job {job_id}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = args[0] if args else None
        if job_id:
            job = Job.query.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.utcnow()
                db.session.commit()
        logger.error(f"Task {task_id} failed: {str(exc)}\n{einfo.traceback}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        job_id = args[0] if args else None
        if job_id:
            job = Job.query.get(job_id)
            if job:
                job.status = JobStatus.RETRYING
                job.progress_message = f"Retrying due to: {str(exc)}"
                db.session.commit()
        logger.warning(f"Task {task_id} being retried: {str(exc)}")

@shared_task(
    bind=True,
    base=BaseJobTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_molecule_job(self, job_id: int):
    """Process a molecule generation job."""
    try:
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.session.commit()

        def update_progress(progress: float, message: str):
            job.progress = progress * 100
            job.progress_message = message
            db.session.commit()

        # Generate molecule
        result_path = generate_collagen_molecule(
            sequence_data=job.parameters.get('sequence_data', {}),
            crosslinks=job.parameters.get('crosslinks'),
            progress_callback=update_progress
        )

        # Update job with results
        job.add_output_file('pdb', result_path)
        return {'status': 'success', 'output_path': result_path}

    except Exception as exc:
        logger.error(f"Error in molecule job {job_id}: {str(exc)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise

@shared_task(
    bind=True,
    base=BaseJobTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_fibril_job(self, job_id: int):
    """Process a fibril generation job."""
    try:
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.session.commit()

        def update_progress(progress: float, message: str):
            job.progress = progress * 100
            job.progress_message = message
            db.session.commit()

        # Create fibril
        result_path, gromacs_files = create_collagen_fibril(
            input_molecule=job.parameters['input_molecule'],
            contact_distance=job.parameters['contact_distance'],
            length=job.parameters['length'],
            generate_gromacs=job.parameters.get('generate_gromacs', False),
            progress_callback=update_progress
        )

        # Update job with results
        job.add_output_file('pdb', result_path)
        if gromacs_files:
            for file_type, path in gromacs_files.items():
                job.add_output_file(file_type, path)

        return {
            'status': 'success',
            'output_path': result_path,
            'gromacs_files': gromacs_files
        }

    except Exception as exc:
        logger.error(f"Error in fibril job {job_id}: {str(exc)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise

@shared_task(
    bind=True,
    base=BaseJobTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def modify_crosslinks_job(self, job_id: int):
    """Process a crosslink modification job."""
    try:
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.session.commit()

        def update_progress(progress: float, message: str):
            job.progress = progress * 100
            job.progress_message = message
            db.session.commit()

        # Modify crosslinks
        result_path = modify_crosslinks(
            input_structure=job.parameters['input_structure'],
            modification_type=job.parameters['modification_type'],
            parameters=job.parameters.get('modification_parameters', {}),
            progress_callback=update_progress
        )

        # Update job with results
        job.add_output_file('pdb', result_path)
        return {'status': 'success', 'output_path': result_path}

    except Exception as exc:
        logger.error(f"Error in crosslink modification job {job_id}: {str(exc)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise

@shared_task
def cleanup_expired_jobs():
    """Clean up expired jobs and their files."""
    try:
        # Find jobs older than 30 days
        expiry_date = datetime.utcnow() - timedelta(days=30)
        expired_jobs = Job.query.filter(Job.created_at < expiry_date).all()

        for job in expired_jobs:
            try:
                # Clean up job files
                if job.output_files:
                    for file_path in job.output_files.values():
                        if os.path.exists(file_path):
                            os.remove(file_path)
                
                # Clean up job directory if it exists
                job_dir = os.path.dirname(list(job.output_files.values())[0]) if job.output_files else None
                if job_dir and os.path.exists(job_dir):
                    shutil.rmtree(job_dir)

                # Mark job as expired in database
                job.status = JobStatus.EXPIRED
                db.session.commit()

            except Exception as e:
                logger.error(f"Error cleaning up job {job.id}: {str(e)}")
                continue

        logger.info(f"Cleaned up {len(expired_jobs)} expired jobs")

    except Exception as e:
        logger.error(f"Error in cleanup_expired_jobs: {str(e)}")
        raise

# Task event handlers
@task_success.connect
def task_success_handler(sender=None, **kwargs):
    logger.info(f"Task {sender.request.id} completed successfully")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    logger.error(f"Task {sender.request.id} failed: {str(exception)}")

@task_retry.connect
def task_retry_handler(sender=None, reason=None, **kwargs):
    logger.warning(f"Task {sender.request.id} is being retried: {str(reason)}")