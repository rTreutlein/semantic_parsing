import os
import networkx as nx
from utils import print_tree

def print_knowledge_graph():
    graph_file = "knowledge_graph.graphml"
    
    if os.path.exists(graph_file):
        print(f"Loading existing knowledge graph from {graph_file}")
        graph = nx.read_graphml(graph_file)
        
        print(f"\nKnowledge Graph:")
        print(f"Number of nodes: {graph.number_of_nodes()}")
        print(f"Number of edges: {graph.number_of_edges()}")
        
        print("\nKnowledge Graph Tree Structure:")
        root_node = next(iter(graph.nodes()))  # Get the first node as the root
        print_tree(graph, root_node)
    else:
        print(f"No knowledge graph file found at {graph_file}")

if __name__ == "__main__":
    print_knowledge_graph()
