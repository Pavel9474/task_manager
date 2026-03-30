import os
import glob
from datetime import datetime, timedelta

def clean_old_logs(log_dir='logs', days=30):
    """Удаляет логи старше указанного количества дней"""
    cutoff = datetime.now() - timedelta(days=days)
    
    log_files = glob.glob(os.path.join(log_dir, '*.log'))
    for log_file in log_files:
        if os.path.getmtime(log_file) < cutoff.timestamp():
            os.remove(log_file)
            print(f"Удалён старый лог: {log_file}")

if __name__ == '__main__':
    clean_old_logs()