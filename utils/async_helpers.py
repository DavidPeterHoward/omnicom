import asyncio
from typing import Any, Callable, Optional, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import threading
import queue
import logging

T = TypeVar('T')

class AsyncResult(Generic[T]):
    def __init__(self):
        self.value: Optional[T] = None
        self.error: Optional[Exception] = None
        self._ready = threading.Event()

    def set_result(self, value: T):
        self.value = value
        self._ready.set()

    def set_error(self, error: Exception):
        self.error = error
        self._ready.set()

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def get(self) -> T:
        self._ready.wait()
        if self.error:
            raise self.error
        return self.value

class AsyncWorker(QThread):
    resultReady = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = AsyncResult()

    def run(self):
        try:
            if asyncio.iscoroutinefunction(self.func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.func(*self.args, **self.kwargs))
                loop.close()
            else:
                result = self.func(*self.args, **self.kwargs)
            self.result.set_result(result)
            self.resultReady.emit(result)
        except Exception as e:
            self.result.set_error(e)
            self.error.emit(e)

class AsyncQueue:
    def __init__(self, max_workers: int = 4):
        self.queue = queue.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._stop = threading.Event()

    def start(self):
        self._stop.clear()
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop(self):
        self._stop.set()
        for _ in range(len(self.workers)):
            self.queue.put(None)
        for worker in self.workers:
            worker.join()
        self.workers.clear()

    def _worker_loop(self):
        while not self._stop.is_set():
            try:
                task = self.queue.get(timeout=0.1)
                if task is None or self._stop.is_set():
                    break
                    
                func, args, kwargs, result = task
                try:
                    if asyncio.iscoroutinefunction(func):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        value = loop.run_until_complete(func(*args, **kwargs))
                        loop.close()
                    else:
                        value = func(*args, **kwargs)
                    result.set_result(value)
                except Exception as e:
                    result.set_error(e)
            except queue.Empty:
                continue

    def submit(self, func: Callable, *args, **kwargs) -> AsyncResult:
        result = AsyncResult()
        self.queue.put((func, args, kwargs, result))
        return result

class AsyncHelper(QObject):
    resultReady = pyqtSignal(object)
    error = pyqtSignal(Exception)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue = AsyncQueue()
        self.queue.start()
        self._active_workers = set()

    def run_async(self, func: Callable, *args, **kwargs) -> AsyncResult:
        worker = AsyncWorker(func, *args, **kwargs)
        worker.resultReady.connect(self._handle_result)
        worker.error.connect(self._handle_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.add(worker)
        worker.start()
        return worker.result

    def submit(self, func: Callable, *args, **kwargs) -> AsyncResult:
        return self.queue.submit(func, *args, **kwargs)

    def _handle_result(self, result):
        self.resultReady.emit(result)

    def _handle_error(self, error):
        self.error.emit(error)

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    def stop(self):
        for worker in list(self._active_workers):
            worker.quit()
            worker.wait()
        self._active_workers.clear()
        self.queue.stop()

class AsyncCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.cache.get(key)

    def set(self, key: str, value: Any):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entries
                remove_count = len(self.cache) // 4
                for k in list(self.cache.keys())[:remove_count]:
                    del self.cache[k]
            self.cache[key] = value

    def clear(self):
        with self.lock:
            self.cache.clear()

def run_async(func: Callable) -> Callable:
    """Decorator to run a function asynchronously in the Qt event loop"""
    def wrapper(*args, **kwargs):
        helper = AsyncHelper()
        return helper.run_async(func, *args, **kwargs)
    return wrapper