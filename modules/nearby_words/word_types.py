from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto

class ResultType(Enum):
    EXACT = auto()
    SPELLING = auto()
    SOUND = auto()
    MEANING = auto()

@dataclass
class WordInfo:
    word: str
    definition: Optional[str] = None
    pos: Optional[str] = None
    frequency: float = 0.0

@dataclass
class SearchResult:
    word: str
    score: float
    result_type: ResultType
    info: Optional[WordInfo] = None