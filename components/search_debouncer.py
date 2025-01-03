from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import asyncio
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
from utils.async_helpers import AsyncHelper

@dataclass
class SearchTask:
    query: str
    timestamp: float
    task_id: str


class EnhancedDebouncer(QObject):
    searchComplete = pyqtSignal(str, list)  # query, results
    searchError = pyqtSignal(str, str)  # query, error message
    searchStarted = pyqtSignal(str)  # query
    searchCancelled = pyqtSignal(str)  # query

    def __init__(self, 
                 delay_ms: int = 300,
                 min_chars: int = 2,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.delay_ms = delay_ms
        self.min_chars = min_chars
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._execute_search)
        
        self.current_task: Optional[SearchTask] = None
        self.search_function: Optional[Callable] = None
        self.async_helper = AsyncHelper(self)
        self.async_helper.resultReady.connect(self._handle_result)
        self.async_helper.error.connect(self._handle_error)

    def set_search_function(self, func: Callable):
        self.search_function = func

    def debounce(self, query: str):
        if not query or len(query) < self.min_chars:
            self.timer.stop()
            if self.current_task:
                self.searchCancelled.emit(self.current_task.query)
                self.current_task = None
            return

        self.timer.stop()
        task_id = f"{time.time()}_{query}"
        self.current_task = SearchTask(query, time.time(), task_id)
        self.timer.start(self.delay_ms)

    def _execute_search(self):
        if not self.current_task or not self.search_function:
            return

        self.searchStarted.emit(self.current_task.query)
        
        if asyncio.iscoroutinefunction(self.search_function):
            self.async_helper.run_async(
                self.search_function,
                self.current_task.query
            )
        else:
            try:
                results = self.search_function(self.current_task.query)
                self._handle_result(results)
            except Exception as e:
                self._handle_error(e)

    def _handle_result(self, results: Any):
        if self.current_task:
            self.searchComplete.emit(self.current_task.query, results)

    def _handle_error(self, error: Exception):
        if self.current_task:
            self.searchError.emit(
                self.current_task.query,
                str(error)
            )

    def stop(self):
        self.timer.stop()
        if self.current_task:
            self.searchCancelled.emit(self.current_task.query)
            self.current_task = None
        self.async_helper.stop()


class SearchManager(QObject):
    resultsReady = pyqtSignal(str, list)  # module_name, results
    searchStarted = pyqtSignal(str)  # module_name
    searchError = pyqtSignal(str, str)  # module_name, error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.debouncers = {}
        self.settings = {
            'delay_ms': 300,
            'min_chars': 2
        }

    def register_module(self, module_name: str, search_function: callable):
        debouncer = EnhancedDebouncer(
            delay_ms=self.settings['delay_ms'],
            min_chars=self.settings['min_chars']
        )
        debouncer.set_search_function(search_function)
        debouncer.searchComplete.connect(
            lambda q, r: self.resultsReady.emit(module_name, r)
        )
        debouncer.searchStarted.connect(
            lambda _: self.searchStarted.emit(module_name)
        )
        debouncer.searchError.connect(
            lambda _, e: self.searchError.emit(module_name, e)
        )
        self.debouncers[module_name] = debouncer

    def search(self, module_name: str, query: str):
        if module_name in self.debouncers:
            self.debouncers[module_name].debounce(query)
            
    def update_settings(self, settings: dict):
        self.settings.update(settings)
        for debouncer in self.debouncers.values():
            debouncer.delay_ms = settings.get('delay_ms', debouncer.delay_ms)
            debouncer.min_chars = settings.get('min_chars', debouncer.min_chars)
            
    def stop_all(self):
        for debouncer in self.debouncers.values():
            debouncer.stop()

