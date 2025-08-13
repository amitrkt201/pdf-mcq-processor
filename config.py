import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    MAX_PAGES = int(os.environ.get('MAX_PAGES', 50))
    UPLOAD_DIR = os.environ.get('UPLOAD_DIR', 'uploads')
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'outputs')
    
    @classmethod
    def init_app(cls, app):
        # Create directories if not exists
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)