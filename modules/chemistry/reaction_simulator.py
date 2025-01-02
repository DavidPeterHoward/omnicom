from typing import List
import logging
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

class ReactionSimulator:
    def __init__(self):
        self.reaction_templates = {
            'addition': '[C:1]=[C:2].[X:3]>>[C:1](-[X:3])-[C:2]',
            'substitution': '[C:1]-[X:2].[Y:3]>>[C:1]-[Y:3]',
            'elimination': '[C:1]-[C:2]-[X:3]>>[C:1]=[C:2].[X:3]',
        }
    
    def predict_products(self, reactants: List[str], reaction_type: str) -> List[str]:
        try:
            if reaction_type not in self.reaction_templates:
                return []
            
            react_mols = [Chem.MolFromSmiles(r) for r in reactants]
            if any(m is None for m in react_mols):
                return []
            
            rxn = AllChem.ReactionFromSmarts(self.reaction_templates[reaction_type])
            products = rxn.RunReactants(react_mols)
            
            result = []
            for product_set in products:
                for product in product_set:
                    smiles = Chem.MolToSmiles(product)
                    if smiles not in result:
                        result.append(smiles)
            
            return result
        except Exception as e:
            logger.error(f"Error predicting products: {e}")
            return []

    def add_reaction_template(self, name: str, smarts: str) -> bool:
        try:
            rxn = AllChem.ReactionFromSmarts(smarts)
            if rxn:
                self.reaction_templates[name] = smarts
                return True
            return False
        except:
            return False

    def get_available_reactions(self) -> List[str]:
        return list(self.reaction_templates.keys())

    def validate_reactants(self, reactants: List[str]) -> bool:
        return all(Chem.MolFromSmiles(r) is not None for r in reactants)