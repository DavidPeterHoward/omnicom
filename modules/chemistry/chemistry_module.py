from typing import List, Dict, Any
import logging
from modules.base_module import EnhancedBaseModule
from modules.chemistry.chemical_structure import ChemicalStructure
from modules.chemistry.structure_viewer import StructureViewer
from rdkit import RDLogger
from utils.async_helpers import AsyncResult
import asyncio
from components.loading_indicator import LoadingIndicator

# Suppress RDKit logging
RDLogger.DisableLog('rdApp.*')

class ChemistryModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.structures = {}
        self.viewer = None
        self._current_query = None
        self._current_task = None
        
        # Default settings
        self._default_settings = {
            'enabled': True,
            'debounce_delay': 300,  # ms
            'min_input_length': 2,
            'auto_show_viewer': True,
            'cache_structures': True,
            'max_cached_structures': 1000
        }
        self.settings.update(self._default_settings)

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

    def get_settings(self) -> List[Dict[str, Any]]:
        return [
            {
                'key': 'enabled',
                'label': 'Enable Chemistry Module',
                'type': 'bool',
                'default': True
            },
            {
                'key': 'debounce_delay',
                'label': 'Search Delay (ms)',
                'type': 'int',
                'min': 0,
                'max': 1000,
                'default': 300
            },
            {
                'key': 'min_input_length',
                'label': 'Minimum Input Length',
                'type': 'int',
                'min': 1,
                'max': 5,
                'default': 2
            },
            {
                'key': 'auto_show_viewer',
                'label': 'Auto-show Structure Viewer',
                'type': 'bool',
                'default': True
            },
            {
                'key': 'cache_structures',
                'label': 'Cache Structures',
                'type': 'bool',
                'default': True
            }
        ]

    async def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        if not query or len(query) < self.settings['min_input_length']:
            return []

        # Create a new task for this query
        task = asyncio.current_task()
        self._current_task = task
        self._current_query = query

        try:
            results = []
            
            # Check cache first if enabled
            if self.settings['cache_structures']:
                if query in self.structures:
                    structure = self.structures[query]
                    return await self._format_results(structure)

            # Create new structure
            structure = await self._create_structure(query)
            
            # Only proceed if this is still the current task
            if task != self._current_task:
                return []

            if structure and structure.mol:
                if self.settings['cache_structures']:
                    self.structures[query] = structure
                
                results = await self._format_results(structure)
                
                # Show structure viewer if enabled
                if self.settings['auto_show_viewer']:
                    await self._show_structure(structure)
            else:
                results.append({
                    "display": f"Could not parse chemical structure: {query}",
                    "value": "",
                    "score": 0
                })

            return results

        except Exception as e:
            self.logger.error(f"Error processing chemistry query: {e}")
            return [{
                "display": f"Error: {str(e)}",
                "value": "",
                "score": 0
            }]
        finally:
            if task == self._current_task:
                self._current_task = None
                self._current_query = None

    async def _create_structure(self, query: str) -> ChemicalStructure:
        """Create chemical structure asynchronously"""
        try:
            # Simulate async operation for non-async ChemicalStructure
            loop = asyncio.get_event_loop()
            structure = await loop.run_in_executor(
                None, 
                ChemicalStructure, 
                query
            )
            return structure
        except Exception as e:
            self.logger.error(f"Error creating structure: {e}")
            return None

    async def _format_results(self, structure: ChemicalStructure) -> List[Dict[str, Any]]:
        """Format structure results asynchronously"""
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

    async def _show_structure(self, structure: ChemicalStructure):
        """Show structure viewer asynchronously"""
        try:
            if not self.viewer:
                self.viewer = StructureViewer()
            
            # Update and show viewer in the main thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: (
                    self.viewer.update_structure(structure),
                    self.viewer.show()
                )
            )
        except Exception as e:
            self.logger.error(f"Error showing structure viewer: {e}")

    def cleanup(self):
        """Cleanup module resources"""
        super().cleanup()
        if self.viewer:
            self.viewer.hide()
            self.viewer.deleteLater()
            self.viewer = None
        
        if self.settings['cache_structures']:
            self.structures.clear()

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "cached_structures": len(self.structures),
            "current_query": self._current_query,
            "is_searching": self._current_task is not None
        }
