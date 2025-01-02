from typing import Set, List, Tuple, Dict, Any
import re
from metaphone import doublemetaphone
from functools import lru_cache

class PhoneticMatcher:
    def __init__(self):
        self.algorithms = {
            'metaphone': self._double_metaphone,
            'refined': self._refined_phonetic
        }
        
        self.phonetic_maps = {
            'metaphone': {},
            'refined': {}
        }
        
        self.weights = {
            'metaphone': 0.7,
            'refined': 0.3
        }

    @staticmethod
    @lru_cache(maxsize=10000)
    def _double_metaphone(word: str) -> Tuple[str, str]:
        return doublemetaphone(word)

    @staticmethod
    @lru_cache(maxsize=10000)
    def _refined_phonetic(word: str) -> str:
        patterns = [
            (r'ght', 't'),
            (r'ph', 'f'),
            (r'qu', 'kw'),
            (r'[aeiou]+', 'a'),
            (r'([^aeiou])\1+', r'\1'),
        ]
        
        word = word.lower()
        for pattern, replacement in patterns:
            word = re.sub(pattern, replacement, word)
        return word

    def add_word(self, word: str):
        primary, secondary = self._double_metaphone(word)
        if primary:
            self.phonetic_maps['metaphone'].setdefault(primary, set()).add(word)
        if secondary:
            self.phonetic_maps['metaphone'].setdefault(secondary, set()).add(word)
        
        refined_code = self._refined_phonetic(word)
        self.phonetic_maps['refined'].setdefault(refined_code, set()).add(word)

    def find_similar(self, word: str) -> List[Tuple[str, float]]:
        matches = {}
        
        for algo_name, algo_func in self.algorithms.items():
            weight = self.weights[algo_name]
            
            if algo_name == 'metaphone':
                primary, secondary = algo_func(word)
                if primary and primary in self.phonetic_maps[algo_name]:
                    for match in self.phonetic_maps[algo_name][primary]:
                        matches[match] = matches.get(match, 0) + weight
                if secondary and secondary in self.phonetic_maps[algo_name]:
                    for match in self.phonetic_maps[algo_name][secondary]:
                        matches[match] = matches.get(match, 0) + weight * 0.8
            else:
                code = algo_func(word)
                if code and code in self.phonetic_maps[algo_name]:
                    for match in self.phonetic_maps[algo_name][code]:
                        matches[match] = matches.get(match, 0) + weight

        if not matches:
            return []
            
        max_score = max(matches.values())
        normalized_matches = [
            (word, score / max_score)
            for word, score in matches.items()
            if word != word
        ]
        
        return sorted(normalized_matches, key=lambda x: x[1], reverse=True)

    def analyze_word(self, word: str) -> Dict[str, Any]:
        return {
            'metaphone': self._double_metaphone(word),
            'refined': self._refined_phonetic(word)
        }