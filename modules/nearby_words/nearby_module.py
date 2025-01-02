from typing import List, Dict, Any
from pathlib import Path
import threading
from PyQt5.QtCore import QTimer
import logging
from modules.base_module import EnhancedBaseModule
from modules.nearby_words.word_index import WordIndex
from modules.nearby_words.word_searcher import InitThread, SearchThread

class NearbyWordsModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.word_index = WordIndex()
        self.search_thread = None
        self.init_thread = None
        self.initialized = False
        self.init_lock = threading.Lock()
        self.search_options = {
            'exact': True,
            'spelling': True,
            'meaning': True
        }
        self._initialize()

    @property
    def name(self) -> str:
        return "Nearby Words"

    @property
    def commands(self) -> List[str]:
        return [":n", ":near", "~"]

    @property
    def example(self) -> str:
        return "happy"

    @property
    def icon(self) -> str:
        return "⦿"

    def _initialize(self):
        if self.initialized:
            return

        with self.init_lock:
            if self.initialized:
                return

            self.init_thread = InitThread(self.word_index)
            self.init_thread.finished.connect(self._initialization_complete)
            self.init_thread.start()

    def _initialization_complete(self):
        self.initialized = True
        self._setup_search_thread()
        self.init_thread = None

    def _setup_search_thread(self):
        if self.search_thread is not None:
            self.search_thread.stop()
            
        self.search_thread = SearchThread(self.word_index)
        self.search_thread.start()

    def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        if not query or len(query) < 2:
            return []

        search_results = self.word_index.search(query, self.search_options)
        
        results = []
        for result in search_results:
            display = f"{result.word} ({int(result.score * 100)}%)"
            if result.info and result.info.definition:
                display += f"\n    {result.info.definition[:100]}..."

            results.append({
                "display": display,
                "value": result.word,
                "score": result.score,
                "type": result.result_type.name
            })

        return results

    def set_search_options(self, options: Dict[str, bool]):
        self.search_options.update(options)

    def clear_cache(self):
        self.word_index.clear_cache()