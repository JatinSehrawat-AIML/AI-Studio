import os
import shutil

def cleanup_directories(dirs: list[str]):
    """
    Deletes all files inside given directories.
    Directory itself is preserved.
    """
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            continue

        for root, _, files in os.walk(dir_path):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except Exception as e:
                    print(f"[WARN] Failed to delete {file}: {e}")
