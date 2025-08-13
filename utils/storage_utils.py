import os
import shutil
import time

def get_storage_info(upload_dir, output_dir):
    def dir_size(path):
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += dir_size(entry.path)
        return total
        
    upload_size = dir_size(upload_dir)
    output_size = dir_size(output_dir)
    
    total_disk = shutil.disk_usage('/').total
    used_disk = shutil.disk_usage('/').used
    free_disk = shutil.disk_usage('/').free
    
    return {
        'upload_dir': {
            'path': upload_dir,
            'file_count': len(os.listdir(upload_dir)),
            'size': upload_size
        },
        'output_dir': {
            'path': output_dir,
            'file_count': len(os.listdir(output_dir)),
            'size': output_size
        },
        'system': {
            'total': total_disk,
            'used': used_disk,
            'free': free_disk
        }
    }

def cleanup_old_files(directories, max_age_hours=1):
    now = time.time()
    deleted_count = 0
    
    for directory in directories:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path):
                continue
                
            file_age = now - os.stat(file_path).st_mtime
            if file_age > max_age_hours * 3600:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except:
                    pass
                    
    return deleted_count