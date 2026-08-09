import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Mengambil URL Redis dari variabel lingkungan Docker
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Menginisialisasi koneksi Worker ke Message Broker
celery_app = Celery(
    "enterprise_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    worker_prefetch_multiplier=1 # Mencegah worker menimbun tugas
)