# app/models/jobs.py

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from app import db
from sqlalchemy.dialects.postgresql import JSON

class JobType(Enum):
    MOLECULE = 'molecule'
    FIBRIL = 'fibril'
    MIXED_CROSSLINKS = 'mixed_crosslinks'
    DENSITY_CHANGE = 'density_change'

class JobStatus(Enum):
    QUEUED = 'queued'         # Initial state when job is created
    RUNNING = 'running'       # Job is being processed
    RETRYING = 'retrying'     # Job failed but will be retried
    COMPLETED = 'completed'   # Job finished successfully
    FAILED = 'failed'        # Job failed and won't be retried
    CANCELLED = 'cancelled'  # Job was cancelled by user
    EXPIRED = 'expired'      # Job has been archived/cleaned up

class Job(db.Model):
    __tablename__ = 'jobs'

    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_type = db.Column(db.Enum(JobType), nullable=False)
    description = db.Column(db.String(120))
    
    # Status and progress tracking
    status = db.Column(db.Enum(JobStatus), default=JobStatus.QUEUED)
    progress = db.Column(db.Float, default=0.0)
    current_step = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Task management
    celery_task_id = db.Column(db.String(255))
    retry_count = db.Column(db.Integer, default=0)
    
    # Job data
    parameters = db.Column(JSON, default=dict)
    input_files = db.Column(JSON, default=dict)
    output_files = db.Column(JSON, default=dict)

    @property
    def is_active(self) -> bool:
        """Check if the job is currently active."""
        return self.status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.RETRYING]

    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            return (end_time - self.started_at).total_seconds()
        return None

    def start_processing(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        db.session.commit()

    def complete(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.progress = 100
        self.completed_at = datetime.utcnow()
        db.session.commit()

    def fail(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        db.session.commit()

    def cancel(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        db.session.commit()

    def update_progress(self, progress: float, step: str) -> None:
        """Update job progress."""
        self.progress = min(max(0, progress), 100)  # Ensure progress is between 0 and 100
        self.current_step = step
        db.session.commit()

    def increment_retry_count(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1
        self.status = JobStatus.RETRYING
        db.session.commit()

    def add_input_file(self, file_type: str, file_path: str) -> None:
        """Add an input file to the job."""
        if not self.input_files:
            self.input_files = {}
        self.input_files[file_type] = file_path
        db.session.commit()

    def add_output_file(self, file_type: str, file_path: str) -> None:
        """Add an output file to the job."""
        if not self.output_files:
            self.output_files = {}
        self.output_files[file_type] = file_path
        db.session.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            'id': self.id,
            'job_type': self.job_type.value,
            'description': self.description,
            'status': self.status.value,
            'progress': self.progress,
            'current_step': self.current_step,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'output_files': list(self.output_files.keys()) if self.output_files else []
        }

    def __repr__(self) -> str:
        return f'<Job {self.id} ({self.job_type.value}): {self.status.value}>'