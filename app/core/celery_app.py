import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

IS_TESTING = os.getenv("TESTING_ENV", "false").lower() == "true"

if IS_TESTING:
    # Enterprise CI/CD Fix: Use in-memory broker during automated testing
    # to avoid dependency on a live Redis server.
    BROKER_URL = "memory://"
    BACKEND_URL = "cache+memory://"
else:
    # Production architecture uses Redis
    BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    BACKEND_URL = BROKER_URL

celery_app = Celery(
    "enterprise_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    worker_prefetch_multiplier=1
)