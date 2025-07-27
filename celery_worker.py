# celery_worker.py

from app import create_app, celery
from app.jobs.celery_config import *  # Import all celery configurations
from celery.signals import worker_ready
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
)
logger = logging.getLogger(__name__)

# Create Flask app instance and push context
app = create_app()
app.app_context().push()

# Configure Celery task routing
celery.conf.update(
    task_routes={
        'app.jobs.tasks.process_molecule_job': {'queue': 'molecular'},
        'app.jobs.tasks.process_fibril_job': {'queue': 'molecular'},
        'app.jobs.tasks.modify_crosslinks_job': {'queue': 'molecular'},
        'app.jobs.tasks.cleanup_expired_jobs': {'queue': 'maintenance'},
    }
)

# Signal handler for worker startup
@worker_ready.connect
def on_worker_ready(**_):
    logger.info('Celery worker is ready for processing tasks')