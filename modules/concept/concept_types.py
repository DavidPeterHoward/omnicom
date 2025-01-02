from dataclasses import dataclass, field
from typing import Set, List, Optional, Any
from enum import Enum, auto
import time


class ConceptType(Enum):
    DIRECT = auto()
    RELATED = auto()
    BROADER = auto()
    NARROWER = auto()
    SIMILAR = auto()

@dataclass
class ConceptInfo:
    name: str
    definition: str
    domains: Set[str] = field(default_factory=set)
    fields: Set[str] = field(default_factory=set)
    topics: Set[str] = field(default_factory=set)
    examples: List[str] = field(default_factory=list)
    synonyms: Set[str] = field(default_factory=set)
    antonyms: Set[str] = field(default_factory=set)
    broader_concepts: Set[str] = field(default_factory=set)
    narrower_concepts: Set[str] = field(default_factory=set)
    related_concepts: Set[str] = field(default_factory=set)
    references: List[str] = field(default_factory=list)
    complexity: int = 1
    score: float = 0.0
    timestamp: float = field(default_factory=time.time)

class SearchFilter:
    def __init__(self, query: str):
        self.original_query = query
        self.parse_filters()

    def parse_filters(self):
        self.domains = set()
        self.excluded_domains = set()
        self.fields = set()
        self.excluded_fields = set()
        self.topics = set()
        self.excluded_topics = set()
        self.commands = {}
        self.terms = []

        parts = self.original_query.split()
        for part in parts:
            if part.startswith('domain:"'):
                domain = part[8:].rstrip('"')
                self.domains.add(domain)
            elif part.startswith('-domain:"'):
                domain = part[9:].rstrip('"')
                self.excluded_domains.add(domain)
            elif part.startswith('field:"'):
                field = part[7:].rstrip('"')
                self.fields.add(field)
            elif part.startswith('-field:"'):
                field = part[8:].rstrip('"')
                self.excluded_fields.add(field)
            elif part.startswith('topic:"'):
                topic = part[7:].rstrip('"')
                self.topics.add(topic)
            elif part.startswith('-topic:"'):
                topic = part[8:].rstrip('"')
                self.excluded_topics.add(topic)
            elif ":" in part:
                command, value = part.split(":", 1)
                if value.startswith('"'):
                    value = value[1:].rstrip('"')
                self.commands[command] = value
            elif part.startswith("-"):
                self.terms.append((part[1:], False))
            else:
                self.terms.append((part, True))