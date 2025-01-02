from typing import List, Dict, Any, Tuple, Any
import networkx as nx
import json
from pathlib import Path
from modules.concept.concept_types import ConceptInfo


class ConceptGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_concept(self, concept: ConceptInfo):
        self.graph.add_node(concept.name, info=concept)
        
        for broader in concept.broader_concepts:
            self.graph.add_edge(broader, concept.name, type="broader")
        
        for narrower in concept.narrower_concepts:
            self.graph.add_edge(concept.name, narrower, type="narrower")
            
        for related in concept.related_concepts:
            self.graph.add_edge(concept.name, related, type="related")

    def get_related_concepts(self, concept_name: str, 
                           max_depth: int = 2) -> List[Tuple[str, str, int]]:
        if concept_name not in self.graph:
            return []

        related = []
        for target in nx.single_source_shortest_path_length(
            self.graph, concept_name, cutoff=max_depth
        ):
            if target != concept_name:
                path = nx.shortest_path(self.graph, concept_name, target)
                relationship_chain = []
                for i in range(len(path)-1):
                    edge_data = self.graph[path[i]][path[i+1]]
                    relationship_chain.append(edge_data["type"])
                
                related.append((
                    target,
                    "->".join(relationship_chain),
                    len(path) - 1
                ))

        return sorted(related, key=lambda x: x[2])

    def get_concept_subgraph(self, concept_name: str, depth: int = 2) -> Dict[str, Any]:
        if concept_name not in self.graph:
            return {"nodes": [], "edges": []}

        nodes = set()
        edges = set()
        
        for target, rel_type, distance in self.get_related_concepts(concept_name, depth):
            nodes.add(concept_name)
            nodes.add(target)
            edges.add((concept_name, target, rel_type))

        return {
            "nodes": [
                {"id": node, "label": node.split(".")[0], 
                 "info": self.graph.nodes[node]["info"].definition[:100]}
                for node in nodes
            ],
            "edges": [
                {"source": src, "target": dst, "type": rel_type}
                for src, dst, rel_type in edges
            ]
        }