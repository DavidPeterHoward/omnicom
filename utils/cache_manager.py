from typing import Any, Dict, Optional, Set
import threading
import pickle
import logging
import time
from pathlib import Path
import json
import weakref


class CacheEntry:
    def __init__(self, value: Any, expire_time: float):
        self.value = value
        self.expire_time = expire_time
        self.access_count = 0
        self.last_access = time.time()

    def is_expired(self) -> bool:
        return time.time() > self.expire_time

    def access(self):
        self.access_count += 1
        self.last_access = time.time()


class ModuleCache:
    def __init__(self, cache_dir: Path, 
                 max_memory_items: int = 1000,
                 max_disk_items: int = 10000,
                 default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_items = max_memory_items
        self.max_disk_items = max_disk_items
        self.default_ttl = default_ttl
        
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache_file = cache_dir / 'cache.pkl'
        self.metadata_file = cache_dir / 'metadata.json'
        
        self.lock = threading.Lock()
        self.stats = {
            'memory_hits': 0,
            'disk_hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        self._load_metadata()
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger('ModuleCache')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.cache_dir / 'cache.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    def _load_metadata(self):
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {'entries': {}}
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
            self.metadata = {'entries': {}}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    def _evict_memory_entries(self):
        """Evict least recently used entries from memory cache"""
        if len(self.memory_cache) <= self.max_memory_items:
            return

        entries = sorted(
            self.memory_cache.items(),
            key=lambda x: (x[1].access_count, x[1].last_access)
        )
        
        # Move oldest entries to disk
        to_evict = len(self.memory_cache) - self.max_memory_items
        for key, entry in entries[:to_evict]:
            if not entry.is_expired():
                self._save_to_disk(key, entry)
            del self.memory_cache[key]
            self.stats['evictions'] += 1

    def _save_to_disk(self, key: str, entry: CacheEntry):
        try:
            # Update metadata
            self.metadata['entries'][key] = {
                'expire_time': entry.expire_time,
                'access_count': entry.access_count,
                'last_access': entry.last_access
            }
            
            # Save the actual data
            cache_file = self.cache_dir / f"{key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry.value, f)
            
            self._save_metadata()
        except Exception as e:
            self.logger.error(f"Error saving to disk: {e}")

    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        try:
            if key not in self.metadata['entries']:
                return None

            meta = self.metadata['entries'][key]
            cache_file = self.cache_dir / f"{key}.pkl"
            
            if not cache_file.exists():
                del self.metadata['entries'][key]
                self._save_metadata()
                return None

            with open(cache_file, 'rb') as f:
                value = pickle.load(f)
                
            entry = CacheEntry(value, meta['expire_time'])
            entry.access_count = meta['access_count']
            entry.last_access = meta['last_access']
            
            return entry if not entry.is_expired() else None

        except Exception as e:
            self.logger.error(f"Error loading from disk: {e}")
            return None

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            # Check memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    entry.access()
                    self.stats['memory_hits'] += 1
                    return entry.value
                else:
                    del self.memory_cache[key]

            # Check disk cache
            entry = self._load_from_disk(key)
            if entry is not None:
                self.memory_cache[key] = entry
                self._evict_memory_entries()
                entry.access()
                self.stats['disk_hits'] += 1
                return entry.value

            self.stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self.lock:
            expire_time = time.time() + (ttl or self.default_ttl)
            entry = CacheEntry(value, expire_time)
            
            self.memory_cache[key] = entry
            self._evict_memory_entries()

    def clear(self):
        with self.lock:
            self.memory_cache.clear()
            
            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    self.logger.error(f"Error clearing cache file {cache_file}: {e}")
            
            self.metadata['entries'].clear()
            self._save_metadata()
            
            self.stats = {
                'memory_hits': 0,
                'disk_hits': 0,
                'misses': 0,
                'evictions': 0
            }

class CacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.base_cache_dir = Path.home() / '.omnibar' / 'cache'
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)
        self.module_caches: Dict[str, ModuleCache] = {}
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger('CacheManager')
        self.logger.setLevel(logging.INFO)
        log_dir = Path.home() / '.omnibar' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / 'cache_manager.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    def get_cache(self, module_name: str) -> ModuleCache:
        if module_name not in self.module_caches:
            cache_dir = self.base_cache_dir / module_name
            self.module_caches[module_name] = ModuleCache(cache_dir)
        return self.module_caches[module_name]

    def clear_all(self):
        for cache in self.module_caches.values():
            cache.clear()

    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        return {
            name: cache.stats.copy()
            for name, cache in self.module_caches.items()
        }

    def cleanup(self):
        """Perform cleanup tasks"""
        for cache in self.module_caches.values():
            cache.clear()
        self.module_caches.clear()