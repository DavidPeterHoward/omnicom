from modules.nearby_words.nearby_module import NearbyWordsModule
from modules.nearby_words.word_types import WordInfo, ResultType, SearchResult
from modules.nearby_words.word_index import WordIndex
from modules.nearby_words.word_searcher import InitThread, SearchThread
from modules.nearby_words.definition_window import DefinitionWindow

__version__ = "1.0.0"

# Module metadata
MODULE_INFO = {
    'name': 'Nearby Words',
    'version': __version__,
    'description': 'Word exploration and relationship discovery',
    'author': 'Omnibar Team',
    'requires': ['nltk', 'rapidfuzz']
}

__all__ = [
    'NearbyWordsModule',
    'WordInfo',
    'ResultType',
    'SearchResult',
    'WordIndex',
    'InitThread',
    'SearchThread',
    'DefinitionWindow',
    'MODULE_INFO'
]
