from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "medprice",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scraping_tasks", "app.tasks.discovery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "daily-full-scrape": {
            "task": "app.tasks.scraping_tasks.run_full_scrape_sync",
            "schedule": crontab(hour=6, minute=0),
            "args": [None],
        },
        "midday-price-refresh": {
            "task": "app.tasks.scraping_tasks.run_full_scrape_sync",
            "schedule": crontab(hour=14, minute=0),
            "args": [None],
        },
        "vendor-discovery-weekly": {
            "task": "app.tasks.discovery_tasks.run_discovery",
            "schedule": crontab(day_of_week=1, hour=8, minute=0),
        },
    },
)
