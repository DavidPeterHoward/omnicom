from typing import List, Dict, Any
import logging
from modules.base_module import EnhancedBaseModule
from modules.chemistry.chemical_structure import ChemicalStructure
from modules.chemistry.structure_viewer import StructureViewer
from rdkit import RDLogger

# Suppress RDKit logging
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

class ChemistryModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.structures = {}
        self.viewer = None

    @property
    def name(self) -> str:
        return "Chemistry"

    @property
    def commands(self) -> List[str]:
        return [":c", ":chem", "⚗"]

    @property
    def example(self) -> str:
        return "CH4"

    @property
    def icon(self) -> str:
        return "⚗"

    def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        if not query:
            return []

        results = []
        
        try:
            if not self.viewer:
                self.viewer = StructureViewer()
            
            # Check cache first
            if query in self.structures:
                structure = self.structures[query]
            else:
                structure = ChemicalStructure(query)
                if structure.mol:  # Only cache valid structures
                    self.structures[query] = structure
            
            if structure.mol:
                results.extend(self._format_results(structure))
                
                # Show structure viewer
                self.viewer.update_structure(structure)
                self.viewer.show()
            else:
                results.append({
                    "display": f"Could not parse chemical structure: {query}",
                    "value": "",
                    "score": 0
                })

        except Exception as e:
            logger.error(f"Error processing chemistry query: {e}")
            results.append({
                "display": f"Error: {str(e)}",
                "value": "",
                "score": 0
            })

        return results

    def _format_results(self, structure: ChemicalStructure) -> List[Dict[str, Any]]:
        results = []
        
        # Basic properties
        results.append({
            "display": f"Formula: {structure.properties['formula']}",
            "value": structure.properties['formula'],
            "score": 1.0,
            "details": {"type": "formula"}
        })
        
        results.append({
            "display": f"Molecular Weight: {structure.properties['molecular_weight']:.2f} g/mol",
            "value": str(structure.properties['molecular_weight']),
            "score": 0.9,
            "details": {"type": "property"}
        })
        
        results.append({
            "display": f"LogP: {structure.properties['logp']:.2f}",
            "value": str(structure.properties['logp']),
            "score": 0.8,
            "details": {"type": "property"}
        })
        
        # pH character
        results.append({
            "display": f"pH Character: {structure.properties['ph_range'].title()}",
            "value": structure.properties['ph_range'],
            "score": 0.7,
            "details": {"type": "property"}
        })
        
        # Acid/Base groups
        if structure.properties['acidic_groups']:
            results.append({
                "display": f"Acidic Groups: {', '.join(structure.properties['acidic_groups'])}",
                "value": ", ".join(structure.properties['acidic_groups']),
                "score": 0.6,
                "details": {"type": "groups"}
            })
            
        if structure.properties['basic_groups']:
            results.append({
                "display": f"Basic Groups: {', '.join(structure.properties['basic_groups'])}",
                "value": ", ".join(structure.properties['basic_groups']),
                "score": 0.6,
                "details": {"type": "groups"}
            })

        # Safety info if available
        safety = structure.properties.get('safety', {})
        if safety.get('safety_summary'):
            results.append({
                "display": f"Safety: {safety['safety_summary']}",
                "value": safety['safety_summary'],
                "score": 0.5,
                "details": {"type": "safety"}
            })

        return results

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "cached_structures": len(self.structures)
        }

    def clear_cache(self):
        self.structures.clear()
        if self.viewer:
            self.viewer.hide()