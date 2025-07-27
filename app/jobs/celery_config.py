# app/jobs/celery_config.py

from celery.schedules import crontab
from kombu import Exchange, Queue
import os

# Broker settings
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Queues
task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('molecular', Exchange('molecular'), routing_key='molecular'),
)

task_default_queue = 'default'
task_default_exchange = 'default'
task_default_routing_key = 'default'

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_acks_late = True
worker_prefetch_multiplier = 1
task_track_started = True
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3300  # 55 minutes

# Result backend settings
result_expires = 60 * 60 * 24  # 24 hours

# Retry settings
task_publish_retry = True
task_publish_retry_policy = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
}

# Error emails
send_task_error_emails = True
admins = [
    ('Admin', os.getenv('ADMIN_EMAIL', 'admin@example.com')),
]

# Monitoring
worker_send_task_events = True
task_send_sent_event = True

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'

# Periodic task settings
beat_schedule = {
    'cleanup-expired-jobs': {
        'task': 'app.jobs.tasks.cleanup_expired_jobs',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}