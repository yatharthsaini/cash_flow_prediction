from __future__ import unicode_literals, absolute_import
import os
import datetime
import inspect
from functools import wraps
from celery import Celery

from django.template.loader import render_to_string
from django.db import models
from django.db.models import QuerySet
from django.core.mail import send_mail
from django.conf import settings

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


def celery_error_email(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        time = datetime.datetime.now()
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            frame = inspect.trace()[-1]
            stack = inspect.stack()
            caller_frame = stack[2]
            caller_function_name = caller_frame.function
            caller_module = caller_frame[0].f_globals['__name__']
            caller_line_number = caller_frame.lineno
            caller_filename = caller_frame.filename

            local_vars = frame[0].f_locals
            variable_data = {var: str(local_vars[var]) for var in local_vars if not isinstance(local_vars[var],
                                                                                               QuerySet)
                             }
            if 'self' in variable_data:
                del variable_data['self']
            data = {
                'server': settings.ENVIRONMENT,
                'caller_function': caller_function_name,
                'caller_module': caller_module,
                'caller_line_number': caller_line_number,
                'caller_filename': caller_filename,
                'line_number': frame[2],
                'code_context': frame[4],
                'error': str(e),
                'variables': variable_data,
            }

            data['func_name'] = func.__name__
            data['func_path'] = frame[0].f_code.co_filename
            data['starting_time'] = time
            data['args'] = args or 'None'
            data['kwargs'] = kwargs or 'None'

            subject = f"Celery task failure ({func.__name__})"
            html_message = render_to_string('celery/celery_error_email.html', data)
            send_mail(
                subject,
                '',
                settings.EMAIL_FROM,
                settings.CELERY_ERROR_EMAIL_LIST,
                fail_silently=False,
                html_message=html_message
            )
            raise
    return wrapper
