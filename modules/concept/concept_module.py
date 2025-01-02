from typing import List, Dict, Any, Optional, Any
import asyncio
import threading
from pathlib import Path
import nltk
from nltk.corpus import wordnet as wn
from modules.base_module import EnhancedBaseModule
from modules.concept.concept_cache import ConceptCache
from modules.concept.concept_graph import ConceptGraph
from modules.concept.concept_searcher import ConceptSearcher
from modules.concept.concept_types import ConceptInfo, SearchFilter
import logging
import wikipedia
import json


class ConceptModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.data_dir = Path.home() / '.omnibar' / 'concepts'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache = ConceptCache(self.data_dir / "cache")
        self.concept_graph = ConceptGraph()
        self.searcher = ConceptSearcher()
        self.initialized = False
        self.lock = threading.Lock()
        self.web_enabled = False

    @property
    def name(self) -> str:
        return "Concepts"

    @property
    def commands(self) -> List[str]:
        return [":c", ":concept", "@"]

    @property
    def example(self) -> str:
        return "quantum physics"

    @property
    def icon(self) -> str:
        return "◎"

    async def _initialize(self):
        if self.initialized:
            return

        async with asyncio.Lock():
            if self.initialized:
                return

            try:
                nltk.download('wordnet', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                
                for synset in wn.all_synsets():
                    concept = await self._create_concept_info(synset)
                    self.searcher.index_concept(concept)
                    self.concept_graph.add_concept(concept)

                self.initialized = True
                
            except Exception as e:
                logging.error(f"Error initializing concept engine: {e}")
                raise

    async def _create_concept_info(self, synset) -> ConceptInfo:
        concept = ConceptInfo(
            name=synset.name(),
            definition=synset.definition(),
            examples=synset.examples(),
            complexity=len(synset.hypernyms()) + 1
        )

        concept.synonyms = {l.name() for l in synset.lemmas()}
        concept.antonyms = {a.name() for l in synset.lemmas() 
                          for a in l.antonyms()}
        concept.broader_concepts = {h.name() for h in synset.hypernyms()}
        concept.narrower_concepts = {h.name() for h in synset.hyponyms()}
        concept.related_concepts = {h.name() for h in synset.similar_tos()}

        domain_terms = []
        domain_terms.extend(d.name().split('.')[0] 
                          for d in synset.topic_domains())
        domain_terms.extend(d.name().split('.')[0] 
                          for d in synset.usage_domains())
        domain_terms.extend(d.name().split('.')[0] 
                          for d in synset.region_domains())

        concept.domains = {d for d in domain_terms if d}
        
        field_terms = []
        for hypernym in synset.closure(lambda s: s.hypernyms()):
            if len(hypernym.name().split('.')) > 1:
                field_terms.append(hypernym.name().split('.')[1])
        concept.fields = {f for f in field_terms if f}

        return concept

    async def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        if not query or len(query) < 2:
            return []

        await self._initialize()

        cache_key = f"search_{query.lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        search_filter = SearchFilter(query)
        
        results = []
        seen = set()
        
        for term, include in search_filter.terms:
            matches = await self.searcher.find_matching_concepts(
                term, search_filter, include)
            for concept_name, score in matches:
                if concept_name not in seen:
                    concept = self.searcher.concepts[concept_name]
                    concept.score = score
                    results.append({
                        "display": f"{concept.name} ({int(score * 100)}%) - {concept.definition[:100]}...",
                        "value": concept.name,
                        "details": {
                            "definition": concept.definition,
                            "examples": concept.examples,
                            "domains": list(concept.domains),
                            "fields": list(concept.fields)
                        },
                        "score": score
                    })
                    seen.add(concept_name)

        for command, value in search_filter.commands.items():
            command_results = await self.searcher.process_command(
                command, value, search_filter)
            for concept_name, score in command_results:
                if concept_name not in seen:
                    concept = self.searcher.concepts[concept_name]
                    concept.score = score
                    results.append({
                        "display": f"{concept.name} ({int(score * 100)}%) - {concept.definition[:100]}...",
                        "value": concept.name,
                        "details": {
                            "definition": concept.definition,
                            "examples": concept.examples,
                            "domains": list(concept.domains),
                            "fields": list(concept.fields)
                        },
                        "score": score
                    })
                    seen.add(concept_name)

        if self.web_enabled:
            try:
                wiki_results = wikipedia.search(query, results=3)
                for title in wiki_results:
                    if title not in seen:
                        try:
                            page = wikipedia.page(title, auto_suggest=False)
                            summary = wikipedia.summary(title, sentences=2)
                            results.append({
                                "display": f"{title} - {summary[:100]}...",
                                "value": title,
                                "details": {
                                    "definition": summary,
                                    "url": page.url,
                                    "source": "wikipedia"
                                },
                                "score": 0.7
                            })
                            seen.add(title)
                        except:
                            continue
            except:
                pass

        results.sort(key=lambda x: (-x["score"], x["value"]))
        results = results[:15]

        self.cache.set(cache_key, results)
        return results

    async def get_concept_details(self, concept_name: str) -> Optional[Dict[str, Any]]:
        if concept_name not in self.searcher.concepts:
            return None

        concept = self.searcher.concepts[concept_name]
        related_concepts = self.concept_graph.get_related_concepts(concept_name)

        return {
            "info": concept,
            "relationships": related_concepts,
            "graph": self.concept_graph.get_concept_subgraph(concept_name)
        }

    def enable_web_search(self, enabled: bool = True):
        self.web_enabled = enabled

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_concepts": len(self.searcher.concepts),
            "total_domains": len(self.searcher.domain_to_concepts),
            "total_fields": len(self.searcher.field_to_concepts),
            "web_enabled": self.web_enabled
        }