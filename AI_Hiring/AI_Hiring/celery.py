import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_hiring.settings')

app = Celery('ai_hiring')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'send-daily-recruiter-summary': {
        'task': 'apps.analytics.tasks.send_daily_summary',
        'schedule': crontab(hour=9, minute=0),
    },
    'auto-reject-expired-applications': {
        'task': 'apps.applications.tasks.auto_reject_expired',
        'schedule': crontab(hour=0, minute=0),
    },
    'send-interview-reminders': {
        'task': 'apps.interviews.tasks.send_reminders',
        'schedule': crontab(minute='*/30'),
    },
}
