from pathlib import Path
from typing import Any, Optional, Dict, Any
import threading
import pickle
import logging
import time


class ConceptCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, Any] = {}
        self.cache_file = self.cache_dir / "concept_cache.pkl"
        self.lock = threading.Lock()
        self.max_memory_items = 10000
        self.load_cache()

    def load_cache(self):
        try:
            if self.cache_file.exists():
                with self.lock:
                    with open(self.cache_file, "rb") as f:
                        self.memory_cache = pickle.load(f)
        except Exception as e:
            logging.error(f"Error loading cache: {e}")
            self.memory_cache = {}

    def save_cache(self):
        try:
            with self.lock:
                with open(self.cache_file, "wb") as f:
                    pickle.dump(self.memory_cache, f)
        except Exception as e:
            logging.error(f"Error saving cache: {e}")

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.memory_cache.get(key)

    def set(self, key: str, value: Any):
        with self.lock:
            self.memory_cache[key] = value
            if len(self.memory_cache) > self.max_memory_items:
                oldest_keys = sorted(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k].timestamp \
                        if hasattr(self.memory_cache[k], 'timestamp') else 0
                )[:self.max_memory_items // 2]
                for k in oldest_keys:
                    del self.memory_cache[k]
            if len(self.memory_cache) % 100 == 0:
                self.save_cache()

    def clear(self):
        with self.lock:
            self.memory_cache.clear()
            self.save_cache()