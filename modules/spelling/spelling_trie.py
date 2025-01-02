from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from rapidfuzz import fuzz

class TrieNode:
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_word: bool = False
        self.frequency: int = 0
        self.word: Optional[str] = None

class SpellingTrie:
    def __init__(self):
        self.root = TrieNode()
        self.word_count = 0
        self.total_frequency = 0
        self.max_frequency = 0
        self.words = set()
        self.by_length = defaultdict(set)
        self.by_first_char = defaultdict(set)

    def insert(self, word: str, frequency: int = 1):
        word = word.lower()
        self.words.add(word)
        self.by_length[len(word)].add(word)
        if word:
            self.by_first_char[word[0]].add(word)

        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        if not node.is_word:
            self.word_count += 1

        node.is_word = True
        node.word = word
        node.frequency += frequency
        self.total_frequency += frequency
        self.max_frequency = max(self.max_frequency, node.frequency)

    def search(self, word: str) -> bool:
        node = self._traverse_to_node(word.lower())
        return bool(node and node.is_word)

    def _traverse_to_node(self, word: str) -> Optional[TrieNode]:
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def get_frequency(self, word: str) -> int:
        node = self._traverse_to_node(word.lower())
        return node.frequency if node and node.is_word else 0

    def find_similar(self, word: str, max_distance: int = 2) -> List[Tuple[str, float]]:
        word = word.lower()
        results = []
        candidates = self._get_candidates(word)

        for candidate in candidates:
            if candidate != word:
                score = self._calculate_similarity(word, candidate)
                if score > 0.6:
                    freq_score = self.get_frequency(candidate) / (self.max_frequency or 1)
                    final_score = score * 0.7 + freq_score * 0.3
                    results.append((candidate, final_score))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def _get_candidates(self, word: str) -> Set[str]:
        word_len = len(word)
        candidates = set()

        for length in range(max(1, word_len - 2), word_len + 3):
            candidates.update(self.by_length[length])

        if word and word[0] in self.by_first_char:
            candidates &= self.by_first_char[word[0]]

        return candidates

    def _calculate_similarity(self, word1: str, word2: str) -> float:
        if abs(len(word1) - len(word2)) > 2:
            return 0.0
        return fuzz.ratio(word1, word2) / 100.0

    def get_statistics(self) -> Dict[str, int]:
        node_count = 0
        max_depth = 0

        def count_nodes(node: TrieNode, depth: int):
            nonlocal node_count, max_depth
            node_count += 1
            max_depth = max(max_depth, depth)
            for child in node.children.values():
                count_nodes(child, depth + 1)

        count_nodes(self.root, 0)

        return {
            "total_words": self.word_count,
            "total_nodes": node_count,
            "max_depth": max_depth,
            "total_frequency": self.total_frequency,
            "max_frequency": self.max_frequency
        }