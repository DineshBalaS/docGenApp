import os, time, shutil
from datetime import datetime, timedelta

GENERATED_DIR = os.path.join(os.path.dirname(__file__), 'generated')
EXPIRE_AFTER_MINUTES = 15

def cleanup_expired_folders():
    now = datetime.now()
    if not os.path.exists(GENERATED_DIR):
        print("Generated directory not found.")
        return

    for folder in os.listdir(GENERATED_DIR):
        path = os.path.join(GENERATED_DIR, folder)
        if os.path.isdir(path):
            modified_time = datetime.fromtimestamp(os.path.getmtime(path))
            if now - modified_time > timedelta(minutes=EXPIRE_AFTER_MINUTES):
                try:
                    shutil.rmtree(path)
                    print(f"🧹 Deleted: {path}")
                except Exception as e:
                    print(f"⚠️ Error deleting {path}: {e}")

if __name__ == '__main__':
    while True:
        print("🔄 Checking for expired folders...")
        cleanup_expired_folders()
        time.sleep(600)  # wait 10 minutes
