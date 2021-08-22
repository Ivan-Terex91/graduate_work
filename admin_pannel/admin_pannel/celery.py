import os

from celery import Celery, shared_task

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_pannel.settings')

app = Celery('admin_pannel')
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@shared_task
def test_task():
    print('Hello from test task')