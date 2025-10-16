"""Thread-safe reader-writer lock implementation."""
import threading
from contextlib import contextmanager
from typing import Generator


class RWLock:
    """
    Reader-Writer lock implementation for concurrent read/write access control.
    
    Features:
    - Multiple readers can acquire the lock simultaneously
    - Writers get exclusive access
    - Fair queuing to prevent writer starvation
    
    Design Choice: Using condition variables for efficient waiting/signaling.
    This prevents busy-waiting and provides fair scheduling.
    """
    
    def __init__(self) -> None:
        """Initialize the reader-writer lock."""
        self._readers = 0
        self._writers = 0
        self._write_waiters = 0
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._write_ready = threading.Condition(self._lock)
    
    @contextmanager
    def read_lock(self) -> Generator[None, None, None]:
        """
        Context manager for acquiring read lock.
        
        Usage:
            with lock.read_lock():
                # Read operations here
                pass
        """
        self._acquire_read()
        try:
            yield
        finally:
            self._release_read()
    
    @contextmanager
    def write_lock(self) -> Generator[None, None, None]:
        """
        Context manager for acquiring write lock.
        
        Usage:
            with lock.write_lock():
                # Write operations here
                pass
        """
        self._acquire_write()
        try:
            yield
        finally:
            self._release_write()
    
    def _acquire_read(self) -> None:
        """Acquire read lock (shared access)."""
        with self._lock:
            # Wait if there are writers or write waiters (prevent writer starvation)
            while self._writers > 0 or self._write_waiters > 0:
                self._read_ready.wait()
            self._readers += 1
    
    def _release_read(self) -> None:
        """Release read lock."""
        with self._lock:
            self._readers -= 1
            # If this was the last reader, notify waiting writers
            if self._readers == 0:
                self._write_ready.notify()
    
    def _acquire_write(self) -> None:
        """Acquire write lock (exclusive access)."""
        with self._lock:
            self._write_waiters += 1
            # Wait until no readers and no other writers
            while self._readers > 0 or self._writers > 0:
                self._write_ready.wait()
            self._write_waiters -= 1
            self._writers = 1
    
    def _release_write(self) -> None:
        """Release write lock."""
        with self._lock:
            self._writers = 0
            # Notify all waiting readers and one writer
            self._write_ready.notify()
            self._read_ready.notify_all()
