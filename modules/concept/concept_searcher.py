from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import asyncio
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import Synset
from rapidfuzz import fuzz
from modules.concept.concept_types import ConceptInfo, SearchFilter
import logging
from utils.cache_manager import CacheManager

class SynsetTracker:
    def __init__(self):
        self.visited: Set[str] = set()
        self.max_depth = 3
        self.current_depth = 0

    def should_visit(self, synset: Synset) -> bool:
        synset_id = synset.name()
        if synset_id in self.visited or self.current_depth > self.max_depth:
            return False
        self.visited.add(synset_id)
        return True

    def enter_level(self):
        self.current_depth += 1

    def exit_level(self):
        self.current_depth -= 1

class ConceptSearcher:
    def __init__(self):
        self.concepts: Dict[str, ConceptInfo] = {}
        self.word_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.domain_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.field_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.topic_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.cache_manager = CacheManager()
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self._setup_wordnet()

    def _setup_wordnet(self):
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            self.initialized = True
        except Exception as e:
            self.logger.error(f"Error setting up WordNet: {e}")
            raise

    async def index_concept(self, concept: ConceptInfo):
        """Index a concept asynchronously"""
        self.concepts[concept.name] = concept

        # Index words
        words = set()
        words.add(concept.name.lower())
        words.update(s.lower() for s in concept.synonyms)
        
        for word in words:
            self.word_to_concepts[word].add(concept.name)

        # Index domains and fields
        for domain in concept.domains:
            self.domain_to_concepts[domain].add(concept.name)
        for field in concept.fields:
            self.field_to_concepts[field].add(concept.name)
        for topic in concept.topics:
            self.topic_to_concepts[topic].add(concept.name)

    async def build_concept_from_synset(self, synset: Synset, 
                                      tracker: Optional[SynsetTracker] = None) -> ConceptInfo:
        """Build concept information from a synset with cycle detection"""
        if tracker is None:
            tracker = SynsetTracker()

        if not tracker.should_visit(synset):
            return None

        try:
            # Check cache first
            cache_key = f"synset_{synset.name()}"
            cached = self.cache_manager.get_cache('concepts').get(cache_key)
            if cached:
                return cached

            concept = ConceptInfo(
                name=synset.name(),
                definition=synset.definition(),
                examples=synset.examples(),
                complexity=len(synset.hypernyms()) + 1
            )

            # Build relationships with depth tracking
            tracker.enter_level()
            
            # Get synonyms and antonyms
            concept.synonyms = {l.name() for l in synset.lemmas()}
            concept.antonyms = {a.name() for l in synset.lemmas() 
                              for a in l.antonyms()}

            # Get related concepts
            if tracker.current_depth < tracker.max_depth:
                # Hypernyms (broader concepts)
                concept.broader_concepts = {h.name() for h in synset.hypernyms() 
                                         if tracker.should_visit(h)}
                
                # Hyponyms (narrower concepts)
                concept.narrower_concepts = {h.name() for h in synset.hyponyms()
                                          if tracker.should_visit(h)}
                
                # Similar concepts
                concept.related_concepts = {h.name() for h in synset.similar_tos()
                                         if tracker.should_visit(h)}

            # Get domains
            domain_terms = []
            domain_terms.extend(d.name().split('.')[0] 
                              for d in synset.topic_domains())
            domain_terms.extend(d.name().split('.')[0] 
                              for d in synset.usage_domains())
            domain_terms.extend(d.name().split('.')[0] 
                              for d in synset.region_domains())

            concept.domains = {d for d in domain_terms if d}
            
            # Get fields
            field_terms = []
            for hypernym in synset.hypernyms():
                if len(hypernym.name().split('.')) > 1:
                    field_terms.append(hypernym.name().split('.')[1])
            concept.fields = {f for f in field_terms if f}

            tracker.exit_level()

            # Cache the result
            self.cache_manager.get_cache('concepts').set(cache_key, concept)
            
            return concept

        except Exception as e:
            self.logger.error(f"Error building concept from synset {synset.name()}: {e}")
            tracker.exit_level()
            return None

    async def find_matching_concepts(
        self, term: str, search_filter: SearchFilter, 
        include: bool = True
    ) -> List[Tuple[str, float]]:
        """Find matching concepts with improved search"""
        matches = []
        seen = set()
        
        # Direct word matches
        if term in self.word_to_concepts:
            for concept_name in self.word_to_concepts[term]:
                concept = self.concepts[concept_name]
                if await self._matches_filters(concept, search_filter):
                    matches.append((concept_name, 1.0))
                    seen.add(concept_name)

        # Fuzzy matches
        for word in self.word_to_concepts:
            if len(word) > 3:
                score = fuzz.ratio(term.lower(), word.lower()) / 100
                if score > 0.7:
                    for concept_name in self.word_to_concepts[word]:
                        if concept_name not in seen:
                            concept = self.concepts[concept_name]
                            if await self._matches_filters(concept, search_filter):
                                matches.append((concept_name, score * 0.9))
                                seen.add(concept_name)

        # Adjust scores based on include flag
        return matches if include else [(m[0], -m[1]) for m in matches]

    async def _matches_filters(self, concept: ConceptInfo, 
                             search_filter: SearchFilter) -> bool:
        """Check if concept matches search filters"""
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

    async def process_command(
        self, command: str, value: str, 
        search_filter: SearchFilter
    ) -> List[Tuple[str, float]]:
        """Process search commands"""
        matches = []

        try:
            if command == "related":
                base_concepts = set()
                for word in value.lower().split():
                    base_concepts.update(self.word_to_concepts.get(word, set()))
                
                for concept_name in base_concepts:
                    concept = self.concepts[concept_name]
                    for related in concept.related_concepts:
                        if related in self.concepts and await self._matches_filters(
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
                        if target in self.concepts and await self._matches_filters(
                            self.concepts[target], search_filter
                        ):
                            matches.append((target, 0.9))

            elif command == "similar":
                # Use fuzzy matching for similar concepts
                for word, concepts in self.word_to_concepts.items():
                    score = fuzz.ratio(value.lower(), word.lower()) / 100
                    if score > 0.7:
                        for concept_name in concepts:
                            if await self._matches_filters(
                                self.concepts[concept_name], 
                                search_filter
                            ):
                                matches.append((concept_name, score * 0.8))

            # Remove duplicates while keeping highest score
            seen = {}
            for name, score in matches:
                if name not in seen or seen[name] < score:
                    seen[name] = score

            return [(name, score) for name, score in seen.items()]

        except Exception as e:
            self.logger.error(f"Error processing command {command}: {e}")
            return []

    async def get_concept_hierarchy(self, concept_name: str, 
                                  max_depth: int = 3) -> Dict[str, Any]:
        """Get hierarchical view of concept relationships"""
        try:
            if concept_name not in self.concepts:
                return None

            cache_key = f"hierarchy_{concept_name}_{max_depth}"
            cached = self.cache_manager.get_cache('concepts').get(cache_key)
            if cached:
                return cached

            tracker = SynsetTracker()
            tracker.max_depth = max_depth

            hierarchy = {
                'name': concept_name,
                'concept': self.concepts[concept_name],
                'broader': [],
                'narrower': [],
                'related': []
            }

            # Get broader concepts (hypernyms)
            for broader in self.concepts[concept_name].broader_concepts:
                if broader in self.concepts and tracker.should_visit(wn.synset(broader)):
                    hierarchy['broader'].append(
                        await self.get_concept_hierarchy(broader, max_depth - 1)
                    )

            # Get narrower concepts (hyponyms)
            tracker = SynsetTracker()  # Reset tracker for hyponyms
            tracker.max_depth = max_depth
            for narrower in self.concepts[concept_name].narrower_concepts:
                if narrower in self.concepts and tracker.should_visit(wn.synset(narrower)):
                    hierarchy['narrower'].append(
                        await self.get_concept_hierarchy(narrower, max_depth - 1)
                    )

            # Get related concepts
            tracker = SynsetTracker()  # Reset tracker for related concepts
            tracker.max_depth = 1  # Limit depth for related concepts
            for related in self.concepts[concept_name].related_concepts:
                if related in self.concepts and tracker.should_visit(wn.synset(related)):
                    hierarchy['related'].append({
                        'name': related,
                        'concept': self.concepts[related]
                    })

            self.cache_manager.get_cache('concepts').set(cache_key, hierarchy)
            return hierarchy

        except Exception as e:
            self.logger.error(f"Error getting concept hierarchy for {concept_name}: {e}")
            return None

    def clear_cache(self):
        """Clear the concept searcher cache"""
        self.cache_manager.get_cache('concepts').clear()