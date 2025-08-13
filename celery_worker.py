import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Set up Celery
celery = Celery('tasks', broker=os.environ.get('REDIS_URL'))
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_max_tasks_per_child=20,
    worker_prefetch_multiplier=1
)

# Import task
from pdf_processor import process_pdf_task

if __name__ == '__main__':
    celery.worker_main()