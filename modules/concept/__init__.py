from modules.concept.concept_module import ConceptModule
from modules.concept.concept_graph import ConceptGraph
from modules.concept.concept_cache import ConceptCache
from modules.concept.concept_searcher import ConceptSearcher
from modules.concept.concept_types import ConceptInfo, ConceptType, SearchFilter
from modules.concept.concept_visualizer import ConceptMindMapView as ConceptVisualizer

__version__ = "1.0.0"

# Module metadata
MODULE_INFO = {
    'name': 'Concepts',
    'version': __version__,
    'description': 'Concept exploration and relationship mapping',
    'author': 'Omnibar Team',
    'requires': ['nltk', 'networkx']
}

__all__ = [
    'ConceptModule',
    'ConceptGraph',
    'ConceptCache',
    'ConceptSearcher',
    'ConceptInfo',
    'ConceptType',
    'SearchFilter',
    'ConceptVisualizer',
    'MODULE_INFO'
]
