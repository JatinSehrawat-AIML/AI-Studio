from pathlib import Path
from typing import Iterable

def cleanup_directories(
    dirs: Iterable[str],
    keep_latest: bool = False
):
    for dir_path in dirs:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            continue

        files = [f for f in path.rglob("*") if f.is_file()]
        if not files:
            continue

        latest = max(files, key=lambda f: f.stat().st_mtime) if keep_latest else None

        for f in files:
            if keep_latest and f == latest:
                continue
            try:
                f.unlink()
            except Exception:
                pass
