from typing import Dict, Optional
import logging
import rdkit
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, rdMolDescriptors, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
import pubchempy as pcp
import re

logger = logging.getLogger(__name__)

class ChemicalStructure:
    # Common chemical formulas and their SMILES
    COMMON_FORMULAS = {
        'CH4': 'C',
        'H2O': 'O',
        'CO2': 'O=C=O',
        'NH3': 'N',
        'BENZENE': 'c1ccccc1',
        'C6H6': 'c1ccccc1',
        'C2H5OH': 'CCO',
        'CH3COOH': 'CC(=O)O',
        'H2SO4': 'O=S(=O)(O)O',
        'HCL': 'Cl',
        'NAOH': '[Na+].[OH-]'
    }

    def __init__(self, query: str = None):
        self.query = query
        self.smiles = None
        self.iupac = None
        self.mol = None
        self.svg = None
        self.properties = {}
        
        if query:
            self._process_input(query)

    def _process_input(self, query: str):
        query = query.upper()
        
        # Try as common formula first
        if query in self.COMMON_FORMULAS:
            self.smiles = self.COMMON_FORMULAS[query]
            self._init_from_smiles()
            return

        # Try as SMILES
        if self._is_valid_smiles(query):
            self.smiles = query
            self._init_from_smiles()
            return

        # Try as IUPAC
        try:
            compounds = pcp.get_compounds(query, 'name')
            if compounds:
                self.smiles = compounds[0].canonical_smiles
                self.iupac = query
                self._init_from_smiles()
        except Exception as e:
            logger.error(f"Error processing input: {e}")

    def _is_valid_smiles(self, smiles: str) -> bool:
        try:
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except:
            return False

    def _init_from_smiles(self):
        try:
            self.mol = Chem.MolFromSmiles(self.smiles)
            if self.mol:
                AllChem.Compute2DCoords(self.mol)
                self._calculate_properties()
                self._generate_svg()
        except Exception as e:
            logger.error(f"Error initializing from SMILES: {e}")

    def _calculate_properties(self):
        try:
            self.properties = {
                'molecular_weight': Descriptors.ExactMolWt(self.mol),
                'formula': Chem.rdMolDescriptors.CalcMolFormula(self.mol),
                'num_atoms': self.mol.GetNumAtoms(),
                'num_bonds': self.mol.GetNumBonds(),
                'num_rings': Chem.rdMolDescriptors.CalcNumRings(self.mol),
                'logp': Descriptors.MolLogP(self.mol),
                'tpsa': Descriptors.TPSA(self.mol),
                'charge': Chem.GetFormalCharge(self.mol)
            }
            
            self._calculate_acid_base_properties()
            self._get_pubchem_data()
        except Exception as e:
            logger.error(f"Error calculating properties: {e}")

    def _calculate_acid_base_properties(self):
        acid_groups = {
            'carboxylic_acid': '[CX3](=O)[OX2H1]',
            'sulfonic_acid': '[SX4](=[OX1])(=[OX1])[OX2H1]',
            'phosphoric_acid': '[PX4](=[OX1])([$([OX2H1]),$([OX1-])])([OX2])([OX2])',
            'phenol': '[cX3]1[cX3H][cX3H][cX3H][cX3H][cX3]1[OX2H1]'
        }
        
        base_groups = {
            'amine': '[NX3;H2,H1;!$(NC=O)]',
            'guanidine': '[NX3][CX3](=[NX2])[NX3]',
            'imidazole': 'c1c[nH]cn1'
        }
        
        self.properties['acidic_groups'] = []
        self.properties['basic_groups'] = []
        
        for name, smarts in acid_groups.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern and self.mol.HasSubstructMatch(pattern):
                self.properties['acidic_groups'].append(name)
        
        for name, smarts in base_groups.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern and self.mol.HasSubstructMatch(pattern):
                self.properties['basic_groups'].append(name)
        
        if self.properties['acidic_groups']:
            self.properties['ph_range'] = 'acidic'
        elif self.properties['basic_groups']:
            self.properties['ph_range'] = 'basic'
        else:
            self.properties['ph_range'] = 'neutral'

    def _get_pubchem_data(self):
        if not self.smiles:
            return
            
        try:
            compounds = pcp.get_compounds(self.smiles, 'smiles')
            if compounds:
                compound = compounds[0]
                self.properties['safety'] = {
                    'ghs_classification': getattr(compound, 'ghs_classification', []),
                    'safety_summary': getattr(compound, 'safety_summary', ''),
                    'toxicity': getattr(compound, 'toxicity', []),
                    'health_hazards': getattr(compound, 'health_hazards', []),
                    'exposure_routes': getattr(compound, 'exposure_routes', []),
                    'first_aid': getattr(compound, 'first_aid', [])
                }
        except Exception as e:
            logger.error(f"Error fetching PubChem data: {e}")
            self.properties['safety'] = {}

    def _generate_svg(self):
        try:
            drawer = rdMolDraw2D.MolDraw2DSVG(400, 400)
            drawer.drawOptions().addAtomIndices = False
            drawer.drawOptions().addStereoAnnotation = True
            drawer.drawOptions().bondLineWidth = 2
            drawer.drawOptions().addRadicals = True
            opts = drawer.drawOptions()
            opts.atomLabelFontSize = 16
            Draw.PrepareAndDrawMolecule(drawer, self.mol)
            drawer.FinishDrawing()
            self.svg = drawer.GetDrawingText()
        except Exception as e:
            logger.error(f"Error generating SVG: {e}")