from typing import List, Dict, Any, Set, Tuple, Optional
from pathlib import Path
import json
import threading
from collections import defaultdict
import nltk
from nltk.corpus import wordnet as wn
import logging
import pickle
import sqlite3
import time
import asyncio
from functools import lru_cache
from rapidfuzz import fuzz, process
import re
from concurrent.futures import ThreadPoolExecutor

from modules.base_module import EnhancedBaseModule
from utils.cache_manager import CacheManager


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

class DictionaryDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Initialize SQLite database for dictionary entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dictionary (
                        word TEXT PRIMARY KEY,
                        definition TEXT,
                        phonetic TEXT,
                        part_of_speech TEXT,
                        frequency REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS synonyms (
                        word TEXT,
                        synonym TEXT,
                        FOREIGN KEY (word) REFERENCES dictionary(word),
                        UNIQUE(word, synonym)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS antonyms (
                        word TEXT,
                        antonym TEXT,
                        FOREIGN KEY (word) REFERENCES dictionary(word),
                        UNIQUE(word, antonym)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            logging.error(f"Error setting up dictionary database: {e}")
            raise

    async def add_word(self, word: str, info: Dict[str, Any]):
        """Add or update a word in the dictionary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert/update main word entry
                cursor.execute("""
                    INSERT OR REPLACE INTO dictionary 
                    (word, definition, phonetic, part_of_speech, frequency)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    word,
                    info.get('definition', ''),
                    info.get('phonetic', ''),
                    info.get('part_of_speech', ''),
                    info.get('frequency', 0.0)
                ))
                
                # Update synonyms
                if 'synonyms' in info:
                    cursor.execute("DELETE FROM synonyms WHERE word = ?", (word,))
                    for synonym in info['synonyms']:
                        cursor.execute("""
                            INSERT OR IGNORE INTO synonyms (word, synonym)
                            VALUES (?, ?)
                        """, (word, synonym))
                
                # Update antonyms
                if 'antonyms' in info:
                    cursor.execute("DELETE FROM antonyms WHERE word = ?", (word,))
                    for antonym in info['antonyms']:
                        cursor.execute("""
                            INSERT OR IGNORE INTO antonyms (word, antonym)
                            VALUES (?, ?)
                        """, (word, antonym))
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error adding word to dictionary: {e}")
            raise

    async def get_word(self, word: str) -> Optional[Dict[str, Any]]:
        """Get word information from dictionary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get main word info
                cursor.execute("""
                    SELECT definition, phonetic, part_of_speech, frequency
                    FROM dictionary
                    WHERE word = ?
                """, (word,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                word_info = {
                    'word': word,
                    'definition': row[0],
                    'phonetic': row[1],
                    'part_of_speech': row[2],
                    'frequency': row[3]
                }
                
                # Get synonyms
                cursor.execute("""
                    SELECT synonym FROM synonyms WHERE word = ?
                """, (word,))
                word_info['synonyms'] = [row[0] for row in cursor.fetchall()]
                
                # Get antonyms
                cursor.execute("""
                    SELECT antonym FROM antonyms WHERE word = ?
                """, (word,))
                word_info['antonyms'] = [row[0] for row in cursor.fetchall()]
                
                return word_info
                
        except Exception as e:
            logging.error(f"Error getting word from dictionary: {e}")
            return None

    async def find_similar(self, word: str, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar words using fuzzy matching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT word FROM dictionary")
                all_words = [row[0] for row in cursor.fetchall()]
                
                similar_words = []
                tasks = []
                
                # Create thread pool for fuzzy matching
                with ThreadPoolExecutor() as executor:
                    loop = asyncio.get_event_loop()
                    
                    # Calculate similarities in parallel
                    for dict_word in all_words:
                        task = loop.run_in_executor(
                            executor,
                            fuzz.ratio,
                            word.lower(),
                            dict_word.lower()
                        )
                        tasks.append((dict_word, task))
                    
                    # Collect results
                    for dict_word, task in tasks:
                        similarity = await task
                        if similarity / 100.0 >= min_similarity:
                            word_info = await self.get_word(dict_word)
                            if word_info:
                                word_info['similarity'] = similarity / 100.0
                                similar_words.append(word_info)
                
                return sorted(
                    similar_words,
                    key=lambda x: (-x['similarity'], -x['frequency'])
                )
                
        except Exception as e:
            logging.error(f"Error finding similar words: {e}")
            return []

class EnhancedSpellingModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.dictionary = DictionaryDatabase(
            Path.home() / '.omnibar' / 'spelling' / 'dictionary.db'
        )
        self.cache_manager = CacheManager()
        self._initialize_nltk()

    def _initialize_nltk(self):
        """Initialize NLTK data"""
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('words', quiet=True)
            nltk.download('cmudict', quiet=True)
        except Exception as e:
            self.logger.error(f"Error initializing NLTK: {e}")
            raise

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

    async def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        """Implementation of search functionality"""
        if not query or len(query) < self.settings.get('min_chars', 2):
            return []

        try:
            # Check cache first
            cache_key = f"spell_{query.lower()}"
            cached = self.cache_manager.get_cache('spelling').get(cache_key)
            if cached:
                return cached

            results = []
            
            # Get word info if it exists
            word_info = await self.dictionary.get_word(query)
            
            if word_info:
                # Word exists, show definition and related words
                results.append({
                    "display": f"✓ {query} is spelled correctly",
                    "value": query,
                    "score": 1.0,
                    "details": word_info
                })
                
                # Add synonyms if available
                if word_info.get('synonyms'):
                    results.append({
                        "display": f"Synonyms: {', '.join(word_info['synonyms'])}",
                        "value": query,
                        "score": 0.9,
                        "details": {"type": "synonyms"}
                    })
                
                # Add antonyms if available
                if word_info.get('antonyms'):
                    results.append({
                        "display": f"Antonyms: {', '.join(word_info['antonyms'])}",
                        "value": query,
                        "score": 0.8,
                        "details": {"type": "antonyms"}
                    })
                
            else:
                # Word not found, show suggestions
                similar_words = await self.dictionary.find_similar(
                    query,
                    min_similarity=self.settings.get('min_similarity', 0.7)
                )
                
                if similar_words:
                    results.append({
                        "display": f"❌ {query} might be misspelled",
                        "value": query,
                        "score": 0.5,
                        "details": {"type": "error"}
                    })
                    
                    for word_info in similar_words:
                        similarity = word_info['similarity']
                        results.append({
                            "display": f"Did you mean: {word_info['word']} ({int(similarity * 100)}%)",
                            "value": word_info['word'],
                            "score": similarity,
                            "details": word_info
                        })
                        
                        # Add quick definition for suggestions
                        if word_info.get('definition'):
                            results.append({
                                "display": f"  → {word_info['definition'][:100]}...",
                                "value": word_info['word'],
                                "score": similarity - 0.01,
                                "details": {"type": "definition"}
                            })

            # Cache results
            if results:
                self.cache_manager.get_cache('spelling').set(cache_key, results)

            return results

        except Exception as e:
            self.logger.error(f"Error processing spelling query: {e}")
            return [{
                "display": f"Error checking spelling: {str(e)}",
                "value": "",
                "score": 0,
                "details": {"type": "error"}
            }]

    def get_settings(self) -> List[Dict[str, Any]]:
        return [
            {
                'key': 'min_chars',
                'label': 'Minimum Characters',
                'type': 'int',
                'min': 1,
                'max': 5,
                'default': 2
            },
            {
                'key': 'min_similarity',
                'label': 'Minimum Similarity',
                'type': 'float',
                'min': 0.5,
                'max': 1.0,
                'default': 0.7
            },
            {
                'key': 'show_definitions',
                'label': 'Show Definitions',
                'type': 'bool',
                'default': True
            },
            {
                'key': 'show_related_words',
                'label': 'Show Related Words',
                'type': 'bool',
                'default': True
            }
        ]

    async def initialize(self):
        """Initialize module async resources"""
        try:
            # Initialize dictionary with WordNet data
            for synset in wn.all_synsets():
                word = synset.name().split('.')[0]
                
                word_info = {
                    'definition': synset.definition(),
                    'part_of_speech': synset.pos(),
                    'synonyms': [l.name() for l in synset.lemmas()],
                    'antonyms': [a.name() for l in synset.lemmas() 
                                for a in l.antonyms()],
                    'frequency': len(synset.lemmas())
                }
                
                await self.dictionary.add_word(word, word_info)
                
        except Exception as e:
            self.logger.error(f"Error initializing spelling module: {e}")
            raise

    def cleanup(self):
        """Cleanup module resources"""
        super().cleanup()
        self.cache_manager.get_cache('spelling').clear()