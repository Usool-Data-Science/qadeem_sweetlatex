import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
environment = os.environ.get("DJANGO_ENV", "dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"sweetlatexBE.settings.{environment}")

app = Celery("sweetlatexBE")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


CELERY_BEAT_SCHEDULE = {
    # Nightly full popularity recomputation — 2 AM UTC
    "recompute-all-popularity": {
        "task": "interactions.recompute_all_popularity",
        "schedule": crontab(hour=2, minute=0),
    },
    # Nightly SASRec retrain — 3 AM UTC (added when recommendations app is done)
    "retrain-sasrec": {
        "task": "recommendations.train_sasrec",
        "schedule": crontab(hour=3, minute=0),
    },
    # Nightly RAG index rebuild — 4 AM UTC (added when chatbot app is done)
    "rebuild-rag-index": {
        "task": "chatbot.rebuild_rag_index",
        "schedule": crontab(hour=4, minute=0),
    },
}
