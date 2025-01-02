from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from pathlib import Path
import json
import logging
import time
from threading import Lock
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.async_helpers import AsyncHelper
from utils.cache_manager import ModuleCache


class ModuleCache:
    def __init__(self, cache_dir: Path, max_age: int = 3600):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = max_age
        self.memory_cache = {}
        self.cache_lock = Lock()
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger('ModuleCache')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.cache_dir / 'cache.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def get(self, key: str) -> Any:
        with self.cache_lock:
            if key in self.memory_cache:
                value, timestamp = self.memory_cache[key]
                if time.time() - timestamp <= self.max_age:
                    return value
                else:
                    del self.memory_cache[key]

            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        if time.time() - data['timestamp'] <= self.max_age:
                            self.memory_cache[key] = (data['value'], data['timestamp'])
                            return data['value']
                        else:
                            cache_file.unlink()
                except Exception as e:
                    self.logger.error(f"Error reading cache for key {key}: {e}")

            return None

    def set(self, key: str, value: Any):
        with self.cache_lock:
            timestamp = time.time()
            self.memory_cache[key] = (value, timestamp)

            cache_file = self.cache_dir / f"{key}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'value': value
                    }, f)
            except Exception as e:
                self.logger.error(f"Error writing cache for key {key}: {e}")

            current_time = time.time()
            self.memory_cache = {
                k: (v, t) for k, (v, t) in self.memory_cache.items()
                if current_time - t <= self.max_age
            }

    def clear(self):
        with self.cache_lock:
            self.memory_cache.clear()
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    cache_file.unlink()
                except Exception as e:
                    self.logger.error(f"Error clearing cache file {cache_file}: {e}")


class EnhancedBaseModule(ABC):
    def __init__(self):
        base_cache_dir = Path.home() / '.omnibar' / 'cache'
        self.cache = ModuleCache(base_cache_dir / self.name.lower())
        self._setup_logging()
        self.settings = {}
        self.async_helper = AsyncHelper()
        self.is_searching = False
        self._current_query: Optional[str] = None

    def _setup_logging(self):
        self.logger = logging.getLogger(f'Module.{self.name}')
        self.logger.setLevel(logging.INFO)
        log_dir = Path.home() / '.omnibar' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / f'{self.name.lower()}.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def commands(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def example(self) -> str:
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        pass

    def get_settings(self) -> List[Dict[str, Any]]:
        """Return list of available settings for this module"""
        return []

    def apply_settings(self, settings: Dict[str, Any]):
        """Apply settings to module"""
        self.settings = settings

    def get_statistics(self) -> Dict[str, Any]:
        """Return module statistics"""
        return {}

    @abstractmethod
    async def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        """Implementation of the search functionality"""
        pass

    async def get_results(self, query: str) -> List[Dict[str, Any]]:
        """Main entry point for getting results"""
        if not self.settings.get('enabled', True):
            return []

        # Check if we should cancel previous search
        if self.is_searching and query != self._current_query:
            self.logger.debug(f"Cancelling previous search for: {self._current_query}")
            # Implement cancellation mechanism here if needed
            self.is_searching = False

        self._current_query = query
        self.is_searching = True

        try:
            # Check cache first
            cache_key = f"search_{query.lower()}"
            cached_results = self.cache.get(cache_key)
            if cached_results is not None:
                return cached_results

            # Get results
            results = await self._get_results_impl(query)

            # Cache results if search completed successfully
            if self.is_searching:  # Only cache if not cancelled
                self.cache.set(cache_key, results)

            return results if self.is_searching else []

        except Exception as e:
            self.logger.error(f"Error getting results for query {query}: {e}")
            return []
        finally:
            if self._current_query == query:  # Only reset if this is the current query
                self.is_searching = False
                self._current_query = None

    def clear_cache(self):
        """Clear module cache"""
        self.cache.clear()

    def cleanup(self):
        """Cleanup module resources"""
        self.async_helper.stop()

    async def initialize(self):
        """Initialize module async resources"""
        pass

    def __del__(self):
        self.cleanup()
