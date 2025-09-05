from app.core.configs.settings import configs

CELERY_CONFIG = {
    'broker_url': configs.CELERY_BROKER_URL,
    'result_backend': configs.CELERY_RESULT_BACKEND,
    'accept_content': ['application/json'],
    'result_accept_content': ['application/json'],
    'timezone': configs.TIMEZONE,
    'task_time_limit': 90,
    'task_max_retries': 3,
    'task_default_retry_delay': 30,
}
