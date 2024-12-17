from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinks.settings')

app = Celery('clinks')

# Load configuration from Django settings.
# - `namespace='CELERY'` ensures all Celery settings in Django settings.py have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery Beat Schedule (Optional, can also be moved to Django settings)
app.conf.beat_schedule = {
    'cancel-driver-not-found-or-expired-orders': {
        'task': 'cancel_driver_not_found_or_expired_orders',
        'schedule': crontab(minute='*/5'),  # Runs every 5 minutes
    },
}