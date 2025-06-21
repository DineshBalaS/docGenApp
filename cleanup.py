import os
import time
from datetime import datetime

GENERATED_DIR = os.path.join(os.path.dirname(__file__), 'generated')
EXPIRY_SECONDS = 5 * 60  # 30 minutes

now = time.time()
deleted_any = False

for folder_name in os.listdir(GENERATED_DIR):
    folder_path = os.path.join(GENERATED_DIR, folder_name)
    if os.path.isdir(folder_path):
        # Use folder modification time
        folder_mtime = os.path.getmtime(folder_path)
        age = now - folder_mtime
        if age > EXPIRY_SECONDS:
            try:
                import shutil
                shutil.rmtree(folder_path)
                print(f"🗑️ Deleted expired folder: {folder_path}")
                deleted_any = True
            except Exception as e:
                print(f"❌ Failed to delete {folder_path}: {e}")

if not deleted_any:
    print("✅ No expired folders found.")
