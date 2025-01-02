from typing import Dict, Set, List, Tuple, Any
import threading
from collections import defaultdict
from functools import lru_cache
from rapidfuzz import fuzz
import nltk
from nltk.corpus import wordnet as wn
from modules.nearby_words.word_types import WordInfo, SearchResult, ResultType

class WordIndex:
    def __init__(self):
        self.words: Dict[str, WordInfo] = {}
        self.prefixes: Dict[str, Set[str]] = defaultdict(set)
        self.by_length: Dict[int, Set[str]] = defaultdict(set)
        self.by_first_char: Dict[str, Set[str]] = defaultdict(set)
        self.initialized = False
        self._lock = threading.Lock()

    def add_word(self, word: str, info: WordInfo):
        with self._lock:
            word = word.lower()
            self.words[word] = info
            
            for i in range(1, len(word) + 1):
                self.prefixes[word[:i]].add(word)
            
            self.by_length[len(word)].add(word)
            
            if word:
                self.by_first_char[word[0]].add(word)

    def search(self, query: str, options: Dict[str, bool]) -> List[SearchResult]:
        query = query.lower()
        results = []
        seen = set()

        with self._lock:
            if options.get('exact', True):
                for word in self.prefixes.get(query, set()):
                    if word not in seen and word != query:
                        results.append(SearchResult(
                            word=word,
                            score=1.0,
                            result_type=ResultType.EXACT,
                            info=self.words.get(word)
                        ))
                        seen.add(word)

            if options.get('spelling', True):
                candidates = self._get_candidates(query)
                for word in candidates:
                    if word not in seen and word != query:
                        score = self._calculate_similarity(query, word)
                        if score > 0.6:
                            results.append(SearchResult(
                                word=word,
                                score=score,
                                result_type=ResultType.SPELLING,
                                info=self.words.get(word)
                            ))
                            seen.add(word)

            if options.get('meaning', True):
                meaning_matches = self._get_meaning_matches(query)
                for word, score in meaning_matches:
                    if word not in seen and word != query and word in self.words:
                        results.append(SearchResult(
                            word=word,
                            score=score,
                            result_type=ResultType.MEANING,
                            info=self.words.get(word)
                        ))
                        seen.add(word)

        results.sort(key=lambda x: (-x.score, x.word))
        return results[:50]

    def _get_candidates(self, word: str) -> Set[str]:
        candidates = set()
        
        word_len = len(word)
        for length in range(max(1, word_len - 2), word_len + 3):
            candidates.update(self.by_length.get(length, set()))
        
        if word and word[0] in self.by_first_char:
            candidates &= self.by_first_char[word[0]]
        
        return candidates

    @lru_cache(maxsize=1000)
    def _calculate_similarity(self, word1: str, word2: str) -> float:
        if not word1 or not word2:
            return 0.0
        if abs(len(word1) - len(word2)) > 2:
            return 0.0
        return fuzz.ratio(word1, word2) / 100.0

    def _get_meaning_matches(self, word: str) -> List[Tuple[str, float]]:
        try:
            matches = []
            for synset in wn.synsets(word):
                for lemma in synset.lemmas():
                    if lemma.name().lower() != word:
                        matches.append((lemma.name().lower(), 0.9))
            return matches
        except Exception:
            return []

    def clear_cache(self):
        self._calculate_similarity.cache_clear()