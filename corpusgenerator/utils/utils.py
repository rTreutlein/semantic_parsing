import networkx as nx
from typing import List

def print_tree(graph: nx.DiGraph, roots: List[str]):
    visited = set()
    for root in roots:
        if root not in visited:
            _print_tree_recursive(graph, root, 0, visited)

def _print_tree_recursive(graph: nx.DiGraph, node: str, level: int, visited: set):
    if node in visited:
        return
    visited.add(node)
    
    for neighbor in graph.neighbors(node):
        edge_data = graph.get_edge_data(node, neighbor)
        print("  " * (level + 1) + f"- [{edge_data['relationship']}] {neighbor}")
        _print_tree_recursive(graph, neighbor, level + 2, visited)

def print_deepest_path(graph: nx.DiGraph, roots: List[str]):
    def dfs(node, path, visited):
        if node in visited:
            return path, len(path)
        visited.add(node)
        
        max_depth = len(path)
        deepest_path = path
        
        for neighbor in graph.neighbors(node):
            edge_data = graph.get_edge_data(node, neighbor)
            new_path, depth = dfs(neighbor, path + [(node, edge_data['relationship'], neighbor)], visited)
            if depth > max_depth:
                max_depth = depth
                deepest_path = new_path
        
        return deepest_path, max_depth

    overall_deepest_path = []
    overall_max_depth = 0

    for root in roots:
        deepest_path, max_depth = dfs(root, [], set())
        if max_depth > overall_max_depth:
            overall_max_depth = max_depth
            overall_deepest_path = deepest_path
    
    print("Deepest path:")
    for i, (source, relationship, target) in enumerate(overall_deepest_path):
        print(f"{'  ' * i}- {source}")
        print(f"{'  ' * (i+1)}[{relationship}]")
    print(f"{'  ' * len(overall_deepest_path)}- {overall_deepest_path[-1][2]}")
