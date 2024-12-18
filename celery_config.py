from celery import Celery
import logging
import os

def setup_celery_logging():
    # Create logs directory if it doesn't exist
    #if not os.path.exists('/download/logs'):
        #os.makedirs('/download/logs')

    # Configure Celery logger
    celery_logger = logging.getLogger('celery')
    celery_logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = logging.FileHandler('/download/logs/celery.log')
    console_handler = logging.StreamHandler()

    # Set level for handlers
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    celery_logger.addHandler(file_handler)
    celery_logger.addHandler(console_handler)

def make_celery(app):
    # Set up logging
    setup_celery_logging()
    logger = logging.getLogger('celery')
    
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    
    # Set some additional common configurations
    celery.conf.update({
        'task_track_started': True,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
        'worker_concurrency': 4,
        'worker_prefetch_multiplier': 1,
        'result_expires': 1209600,
        # Add logging configuration
        'worker_log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'worker_task_log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'worker_redirect_stdouts': False,
        'worker_redirect_stdouts_level': 'DEBUG',
    })

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                logger.debug(f"Task args: {args}")
                logger.debug(f"Task kwargs: {kwargs}")
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
