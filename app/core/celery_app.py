import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

IS_TESTING = os.getenv("TESTING_ENV", "false").lower() == "true"

if IS_TESTING:
    # Enterprise CI/CD Fix: 'cache+memory://' is an invalid Celery backend.
    # We use 'memory://' for the broker and 'rpc://' for the backend, 
    # combined with eager execution to bypass Redis completely.
    BROKER_URL = "memory://"
    BACKEND_URL = "rpc://"
else:
    # Production architecture uses Redis
    BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    BACKEND_URL = BROKER_URL

celery_app = Celery(
    "enterprise_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    # INJEKSI MEMORI TUGAS: Memaksa Worker membaca fungsi saat booting
    include=["app.core.tasks", "app.services.tasks"] 
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    # Force synchronous execution during unit testing
    task_always_eager=IS_TESTING, 
    task_eager_propagates=IS_TESTING
)