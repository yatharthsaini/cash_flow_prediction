import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cash_flow_prediction.settings')

app = Celery('cash_flow_prediction')

BASE_REDIS_URL = os.environ.get('REDIS_URL')

app.config_from_object('django.conf:settings', namespace='CELERY')

# celery.py or settings.py or wherever you set Celery settings
app.conf.broker_connection_retry_on_startup = True

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.broker_url = BASE_REDIS_URL

app.conf.beat_scheduler = "django_celery_beat.schedulers.DatabaseScheduler"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
