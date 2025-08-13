import os
import re
import uuid
import shutil
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from celery import Celery
import psutil

app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret'),
    UPLOAD_DIR='uploads',
    OUTPUT_DIR='outputs',
    MAX_PAGES=int(os.environ.get('MAX_PAGES', 50)),
    REDIS_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    ALLOWED_EXTENSIONS={'pdf'}
)

# Create directories
os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)

# Initialize Celery
celery = Celery(app.name, broker=app.config['REDIS_URL'])
celery.conf.update(app.config)

# Import processing functions
from pdf_processor import process_pdf_task
from utils.storage_utils import get_storage_info, cleanup_old_files
from utils.ocr_utils import enhance_image_for_ocr
from utils.language_utils import separate_languages

@app.route('/')
def health_check():
    return jsonify(status='active', timestamp=datetime.utcnow())

@app.route('/api/process', methods=['POST'])
def handle_process():
    # Validate request
    if 'type' not in request.json or 'options' not in request.json:
        return jsonify(error="Missing required parameters"), 400
    
    pdf_type = request.json['type']
    options = request.json['options']
    files = request.json.get('files', [])
    
    # Validate page limits
    start_page = options.get('start_page', 0)
    end_page = options.get('end_page', app.config['MAX_PAGES'])
    if end_page - start_page > app.config['MAX_PAGES']:
        return jsonify(error=f"Page limit exceeded (max {app.config['MAX_PAGES']})"), 400
    
    # Create processing task
    task = process_pdf_task.apply_async(args=[pdf_type, files, options])
    return jsonify(task_id=task.id)

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = process_pdf_task.AsyncResult(task_id)
    
    response = {
        'state': task.state,
        'task_id': task_id
    }
    
    if task.state == 'PROGRESS':
        response.update(task.info)
    elif task.state == 'SUCCESS':
        response['result'] = task.result
    elif task.state == 'FAILURE':
        response['error'] = str(task.info)
    
    return jsonify(response)

@app.route('/api/download/<task_id>', methods=['GET'])
def download_results(task_id):
    file_type = request.args.get('type', 'csv')
    filename = f"{app.config['OUTPUT_DIR']}/{task_id}"
    
    if file_type == 'hindi':
        return send_file(f"{filename}_hindi.csv", as_attachment=True)
    elif file_type == 'english':
        return send_file(f"{filename}_english.csv", as_attachment=True)
    elif file_type == 'excel':
        return send_file(f"{filename}.xlsx", as_attachment=True)
    elif file_type == 'images':
        return send_file(f"{filename}_images.zip", as_attachment=True)
    else:
        return jsonify(error="Invalid file type"), 400

@app.route('/api/storage', methods=['GET'])
def storage_info():
    return jsonify(get_storage_info(app.config['UPLOAD_DIR'], app.config['OUTPUT_DIR']))

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    deleted = cleanup_old_files(
        [app.config['UPLOAD_DIR'], app.config['OUTPUT_DIR']], 
        max_age_hours=1
    )
    return jsonify(deleted=deleted)

@app.route('/api/resources', methods=['GET'])
def resource_usage():
    return jsonify({
        'memory': psutil.virtual_memory()._asdict(),
        'cpu': psutil.cpu_percent(),
        'disk': shutil.disk_usage('/')._asdict()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)