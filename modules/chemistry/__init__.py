from modules.chemistry.chemistry_module import ChemistryModule
from modules.chemistry.chemical_structure import ChemicalStructure
from modules.chemistry.structure_viewer import StructureViewer
from modules.chemistry.reaction_simulator import ReactionSimulator

__version__ = "1.0.0"

# Module metadata
MODULE_INFO = {
    'name': 'Chemistry',
    'version': __version__,
    'description': 'Chemical structure visualization and analysis',
    'author': 'Omnibar Team',
    'requires': ['rdkit', 'pubchempy']
}

__all__ = [
    'ChemistryModule',
    'ChemicalStructure',
    'StructureViewer',
    'ReactionSimulator',
    'MODULE_INFO'
]
