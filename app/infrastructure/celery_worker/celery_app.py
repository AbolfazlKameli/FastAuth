from celery import Celery

from .celery_configs import CELERY_CONFIG

celery_app = Celery(__name__)
celery_app.conf.update(CELERY_CONFIG)
