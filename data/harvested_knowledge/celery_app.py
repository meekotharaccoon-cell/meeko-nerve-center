"""
Celery application for background tasks
"""

from celery import Celery
from celery.schedules import crontab
from ..config.settings import settings

# Create Celery app
celery_app = Celery(
    "pod_ecommerce",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.email.*": {"queue": "email"},
        "app.tasks.image.*": {"queue": "image_processing"},
        "app.tasks.print.*": {"queue": "print_production"},
        "app.tasks.notification.*": {"queue": "notifications"},
    },
    beat_schedule={
        "send-daily-reports": {
            "task": "app.tasks.analytics.send_daily_reports",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        "cleanup-old-designs": {
            "task": "app.tasks.design.cleanup_old_designs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "update-inventory": {
            "task": "app.tasks.inventory.update_inventory_levels",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "send-low-stock-alerts": {
            "task": "app.tasks.inventory.send_low_stock_alerts",
            "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
        },
    }
)

if __name__ == "__main__":
    celery_app.start()
