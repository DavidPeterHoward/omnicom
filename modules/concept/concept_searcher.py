from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import nltk
from nltk.tokenize import word_tokenize
from rapidfuzz import fuzz
from modules.concept.concept_types import ConceptInfo, SearchFilter


class ConceptSearcher:
    def __init__(self):
        self.concepts: Dict[str, ConceptInfo] = {}
        self.word_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.domain_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.field_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.topic_to_concepts: Dict[str, Set[str]] = defaultdict(set)

    def index_concept(self, concept: ConceptInfo):
        self.concepts[concept.name] = concept

        words = set()
        words.add(concept.name.lower())
        words.update(s.lower() for s in concept.synonyms)
        for word in words:
            self.word_to_concepts[word].add(concept.name)

        for domain in concept.domains:
            self.domain_to_concepts[domain].add(concept.name)
        for field in concept.fields:
            self.field_to_concepts[field].add(concept.name)
        for topic in concept.topics:
            self.topic_to_concepts[topic].add(concept.name)

    def find_matching_concepts(
        self, term: str, search_filter: SearchFilter, 
        include: bool = True
    ) -> List[Tuple[str, float]]:
        matches = []
        
        if term in self.word_to_concepts:
            for concept_name in self.word_to_concepts[term]:
                concept = self.concepts[concept_name]
                if self._matches_filters(concept, search_filter):
                    matches.append((concept_name, 1.0))

        for word in self.word_to_concepts:
            if len(word) > 3:
                score = fuzz.ratio(term.lower(), word.lower()) / 100
                if score > 0.7:
                    for concept_name in self.word_to_concepts[word]:
                        concept = self.concepts[concept_name]
                        if self._matches_filters(concept, search_filter):
                            matches.append((concept_name, score * 0.9))

        return matches if include else [(m[0], -m[1]) for m in matches]

    def _matches_filters(self, concept: ConceptInfo, search_filter: SearchFilter) -> bool:
        if search_filter.domains and not (concept.domains & search_filter.domains):
            return False
        if search_filter.excluded_domains and (concept.domains & search_filter.excluded_domains):
            return False

        if search_filter.fields and not (concept.fields & search_filter.fields):
            return False
        if search_filter.excluded_fields and (concept.fields & search_filter.excluded_fields):
            return False

        if search_filter.topics and not (concept.topics & search_filter.topics):
            return False
        if search_filter.excluded_topics and (concept.topics & search_filter.excluded_topics):
            return False

        return True

    def process_command(
        self, command: str, value: str, 
        search_filter: SearchFilter
    ) -> List[Tuple[str, float]]:
        matches = []

        if command == "related":
            base_concepts = set()
            for word in value.lower().split():
                base_concepts.update(self.word_to_concepts.get(word, set()))
            
            for concept_name in base_concepts:
                concept = self.concepts[concept_name]
                for related in concept.related_concepts:
                    if related in self.concepts and self._matches_filters(
                        self.concepts[related], search_filter
                    ):
                        matches.append((related, 0.9))

        elif command in ["broader", "narrower"]:
            base_concepts = set()
            for word in value.lower().split():
                base_concepts.update(self.word_to_concepts.get(word, set()))
            
            for concept_name in base_concepts:
                concept = self.concepts[concept_name]
                target_concepts = (concept.broader_concepts if command == "broader" 
                                 else concept.narrower_concepts)
                
                for target in target_concepts:
                    if target in self.concepts and self._matches_filters(
                        self.concepts[target], search_filter
                    ):
                        matches.append((target, 0.9))

        elif command == "similar":
            for word, concepts in self.word_to_concepts.items():
                score = fuzz.ratio(value.lower(), word.lower()) / 100
                if score > 0.7:
                    for concept_name in concepts:
                        if self._matches_filters(self.concepts[concept_name], search_filter):
                            matches.append((concept_name, score * 0.8))

        return matches