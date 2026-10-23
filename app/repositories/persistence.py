"""Crash-safe snapshot writes shared by the repositories."""
import os
import pickle
from pathlib import Path
from typing import Any


def atomic_pickle_dump(obj: Any, path: Path) -> None:
    """Write a pickle snapshot so a crash leaves either the old or the new file.
    
    Steps:
    1. Pickle to a temp file in the same directory
    2. fsync the temp file so its bytes are on disk before it becomes visible
    3. os.replace it over the target (atomic on POSIX and Windows)
    4. fsync the directory (POSIX) so the rename itself survives a power loss
    
    Args:
        obj: Object to pickle
        path: Final file path
    """
    path = Path(path)
    temp_path = path.with_suffix('.tmp')
    
    with open(temp_path, 'wb') as f:
        pickle.dump(obj, f)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(temp_path, path)
    
    # Directory fsync is not supported on Windows; the rename is still atomic there
    if os.name == 'posix':
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
