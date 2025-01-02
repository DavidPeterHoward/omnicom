import time
from typing import Any, Optional, Dict
import threading
import pickle
from pathlib import Path

class MultiLevelCache:
    def __init__(self, cache_dir: Path, max_memory_items: int = 1000,
                 disk_cache_size: int = 10000, ttl: int = 3600):
        self.cache_dir = cache_dir
        self.max_memory_items = max_memory_items
        self.disk_cache_size = disk_cache_size
        self.ttl = ttl
        
        self.memory_cache: Dict[str, tuple] = {}
        self.memory_lru: list = []
        
        self.disk_cache_file = cache_dir / 'spelling_cache.pkl'
        self.disk_cache: Dict[str, tuple] = self._load_disk_cache()
        
        self.cache_lock = threading.Lock()
        
        self.stats = {
            'memory_hits': 0,
            'disk_hits': 0,
            'misses': 0
        }

    def _load_disk_cache(self) -> Dict[str, tuple]:
        if self.disk_cache_file.exists():
            try:
                with open(self.disk_cache_file, 'rb') as f:
                    cache = pickle.load(f)
                now = time.time()
                cache = {
                    k: v for k, v in cache.items()
                    if now - v[1] < self.ttl
                }
                return cache
            except Exception:
                return {}
        return {}

    def _save_disk_cache(self):
        try:
            with open(self.disk_cache_file, 'wb') as f:
                pickle.dump(self.disk_cache, f)
        except Exception:
            pass

    def _update_memory_lru(self, key: str):
        if key in self.memory_lru:
            self.memory_lru.remove(key)
        self.memory_lru.append(key)
        
        while len(self.memory_lru) > self.max_memory_items:
            evicted_key = self.memory_lru.pop(0)
            if evicted_key in self.memory_cache:
                self.disk_cache[evicted_key] = self.memory_cache[evicted_key]
                del self.memory_cache[evicted_key]

    def get(self, key: str) -> Optional[Any]:
        with self.cache_lock:
            now = time.time()
            
            if key in self.memory_cache:
                value, timestamp = self.memory_cache[key]
                if now - timestamp < self.ttl:
                    self._update_memory_lru(key)
                    self.stats['memory_hits'] += 1
                    return value
                else:
                    del self.memory_cache[key]
            
            if key in self.disk_cache:
                value, timestamp = self.disk_cache[key]
                if now - timestamp < self.ttl:
                    self.memory_cache[key] = (value, timestamp)
                    self._update_memory_lru(key)
                    self.stats['disk_hits'] += 1
                    return value
                else:
                    del self.disk_cache[key]
            
            self.stats['misses'] += 1
            return None

    def set(self, key: str, value: Any):
        with self.cache_lock:
            now = time.time()
            
            self.memory_cache[key] = (value, now)
            self._update_memory_lru(key)
            
            if len(self.disk_cache) >= self.disk_cache_size:
                sorted_items = sorted(self.disk_cache.items(), 
                                   key=lambda x: x[1][1])
                self.disk_cache = dict(sorted_items[len(sorted_items)//2:])
            
            if self.stats['misses'] % 100 == 0:
                self._save_disk_cache()

    def clear(self):
        with self.cache_lock:
            self.memory_cache.clear()
            self.memory_lru.clear()
            self.disk_cache.clear()
            self._save_disk_cache()
            self.stats = {
                'memory_hits': 0,
                'disk_hits': 0,
                'misses': 0
            }

    def get_stats(self) -> Dict[str, Any]:
        with self.cache_lock:
            total_hits = self.stats['memory_hits'] + self.stats['disk_hits']
            total_requests = total_hits + self.stats['misses']
            
            return {
                'memory_cache_size': len(self.memory_cache),
                'disk_cache_size': len(self.disk_cache),
                'memory_hit_rate': self.stats['memory_hits'] / total_requests if total_requests else 0,
                'disk_hit_rate': self.stats['disk_hits'] / total_requests if total_requests else 0,
                'total_hit_rate': total_hits / total_requests if total_requests else 0,
                'stats': dict(self.stats)
            }