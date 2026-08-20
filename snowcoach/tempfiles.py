"""Utilities for cleaning up temporary media files."""

from __future__ import annotations

import gc
import time
from pathlib import Path


def remove_temp_file(path: str | Path, *, attempts: int = 5, delay: float = 0.1) -> bool:
    """Remove *path*, retrying when another process temporarily holds it.

    OpenCV/Windows can retain a video file handle briefly after ``release``.  A
    cleanup failure must not turn an otherwise successful analysis into an app
    error, so sharing violations are retried and ultimately reported to the
    caller instead of being raised.
    """
    temporary_path = Path(path)
    for attempt in range(attempts):
        try:
            temporary_path.unlink(missing_ok=True)
            return True
        except PermissionError:
            if attempt == attempts - 1:
                return False
            gc.collect()
            time.sleep(delay * (attempt + 1))
    return False
