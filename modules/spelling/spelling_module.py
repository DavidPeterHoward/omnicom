from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
import json
import threading
from collections import defaultdict
import nltk
import pickle
import time
from functools import lru_cache
from rapidfuzz import fuzz, process
import re
from modules.base_module import EnhancedBaseModule

class FastTrie:
    def __init__(self):
        self.words = set()
        self.word_freq = {}
        self.word_by_length = defaultdict(set)
        self.first_char_index = defaultdict(set)
        self.max_freq = 1

    def insert_batch(self, word_dict: Dict[str, int]):
        for word, freq in word_dict.items():
            word = word.lower()
            self.words.add(word)
            self.word_freq[word] = freq
            self.word_by_length[len(word)].add(word)
            self.first_char_index[word[0]].add(word)
            self.max_freq = max(self.max_freq, freq)

    def search(self, word: str) -> bool:
        return word.lower() in self.words

    def get_frequency(self, word: str) -> int:
        return self.word_freq.get(word.lower(), 0)

    def get_similar_by_length(self, word: str, length_diff: int = 2) -> Set[str]:
        word_len = len(word)
        candidates = set()
        for length in range(max(1, word_len - length_diff), word_len + length_diff + 1):
            candidates.update(self.word_by_length[length])
        return {w for w in candidates if w[0] == word[0]}

class FastCache:
    def __init__(self, cache_size: int = 10000):
        self.cache = {}
        self.timestamps = {}
        self.max_size = cache_size
        self.lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self.lock:
            if key in self.cache:
                self.timestamps[key] = time.time()
                return self.cache[key]
            return None

    def set(self, key: str, value: Any):
        with self.lock:
            now = time.time()
            self.cache[key] = value
            self.timestamps[key] = now
            
            if len(self.cache) > self.max_size:
                oldest = sorted(self.timestamps.items(), key=lambda x: x[1])[:-self.max_size]
                for key, _ in oldest:
                    del self.cache[key]
                    del self.timestamps[key]

class TypeDebouncer:
    def __init__(self, delay: float = 0.2):
        self.delay = delay
        self.last_type = 0
        self.lock = threading.Lock()

    def should_process(self) -> bool:
        with self.lock:
            now = time.time()
            if now - self.last_type >= self.delay:
                self.last_type = now
                return True
            return False

class SpellingModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.trie = FastTrie()
        self.cache = FastCache()
        self.debouncer = TypeDebouncer()
        self.custom_words = set()
        self.custom_freq = {}
        self.init_lock = threading.Lock()
        self._initialized = False

    @property
    def name(self) -> str:
        return "Spelling"

    @property
    def commands(self) -> List[str]:
        return [":s", ":spell", "?"]

    @property
    def example(self) -> str:
        return "accomodate"

    @property
    def icon(self) -> str:
        return "✓"

    def _ensure_initialized(self):
        if not self._initialized:
            with self.init_lock:
                if not self._initialized:
                    self._initialize_data()
                    self._initialized = True

    def _initialize_data(self):
        try:
            nltk.data.find('corpora/words')
            nltk.data.find('corpora/brown')
        except LookupError:
            nltk.download('words', quiet=True)
            nltk.download('brown', quiet=True)

        cache_file = Path.home() / '.omnibar' / 'spelling' / 'word_data.pkl'
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
                self.trie.insert_batch(data)
                return

        from nltk.corpus import words, brown
        word_freq = defaultdict(int)
        
        for word in brown.words():
            if word.isalpha():
                word_freq[word.lower()] += 1

        word_dict = {word.lower(): word_freq[word.lower()] 
                    for word in words.words() 
                    if word.isalpha()}

        self.trie.insert_batch(word_dict)

        with open(cache_file, 'wb') as f:
            pickle.dump(word_dict, f)

    @lru_cache(maxsize=1000)
    def _quick_similarity(self, s1: str, s2: str) -> float:
        if abs(len(s1) - len(s2)) > 2:
            return 0.0
        if s1[0] != s2[0]:
            return 0.0
        return fuzz.ratio(s1, s2) / 100.0

    def _get_similar_words(self, word: str) -> List[Tuple[str, float]]:
        candidates = self.trie.get_similar_by_length(word, length_diff=1)
        results = []
        
        for candidate in candidates:
            if candidate != word:
                score = self._quick_similarity(word, candidate)
                if score > 0.6:
                    freq_boost = min(1.0, self.trie.get_frequency(candidate) / self.trie.max_freq)
                    final_score = score * 0.7 + freq_boost * 0.3
                    results.append((candidate, final_score))

        return sorted(results, key=lambda x: x[1], reverse=True)[:10]

    def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        if not self.debouncer.should_process():
            return []

        self._ensure_initialized()
        
        word = query.strip().lower()
        if not word or len(word) < 2:
            return []

        cache_key = f"spell_{word}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if self.trie.search(word):
            return []

        similar = self._get_similar_words(word)
        
        results = [{
            "display": f"{w} ({int(score * 100)}% match)",
            "value": w,
            "score": score,
            "source": "custom" if w in self.custom_words else "dictionary"
        } for w, score in similar]

        self.cache.set(cache_key, results)
        return results

    def add_to_custom_dictionary(self, word: str):
        self._ensure_initialized()
        word = word.lower()
        self.custom_words.add(word)
        self.custom_freq[word] = self.trie.max_freq
        self.trie.insert_batch({word: self.trie.max_freq})
        self._quick_similarity.cache_clear()

    def clear_cache(self):
        self.cache = FastCache()
        self._quick_similarity.cache_clear()

    def analyze_text(self, text: str) -> Dict[str, Any]:
        self._ensure_initialized()
        words = [w for w in text.split() if w.isalpha()]
        misspelled = []

        for i, word in enumerate(words):
            if not self.trie.search(word.lower()):
                similar = self._get_similar_words(word.lower())
                if similar:
                    misspelled.append({
                        "word": word,
                        "position": i,
                        "suggestions": similar[:5],
                        "error_type": "unknown"
                    })

        return {
            "total_words": len(words),
            "unique_words": len(set(words)),
            "errors": misspelled,
            "error_rate": len(misspelled) / len(words) if words else 0
        }