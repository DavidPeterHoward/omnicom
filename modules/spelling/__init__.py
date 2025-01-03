from modules.spelling.spelling_module import EnhancedSpellingModule as SpellingModule, DictionaryDatabase
from modules.spelling.spelling_cache import MultiLevelCache
from modules.spelling.spelling_photonic_matching import PhoneticMatcher
from modules.spelling.spelling_trie import SpellingTrie

__version__ = "1.0.0"

# Module metadata
MODULE_INFO = {
    'name': 'Spelling',
    'version': __version__,
    'description': 'Spelling correction and dictionary integration',
    'author': 'Omnibar Team',
    'requires': ['nltk', 'rapidfuzz', 'sqlite3']
}

__all__ = [
    'SpellingModule',
    'MultiLevelCache',
    'PhoneticMatcher',
    'DictionaryDatabase',
    'SpellingTrie',
    'MODULE_INFO'
]