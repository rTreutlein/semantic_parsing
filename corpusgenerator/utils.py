import networkx as nx

def print_tree(graph: nx.DiGraph, node: str, level: int = 0, visited: set = None):
    if visited is None:
        visited = set()
    
    if node in visited:
        return
    visited.add(node)
    
    if level == 0:
        print("  " * level + f"- {node}")
    for neighbor in graph.neighbors(node):
        edge_data = graph.get_edge_data(node, neighbor)
        print("  " * (level + 1) + f"- [{edge_data['relationship']}] {neighbor}")
        print_tree(graph, neighbor, level + 2, visited)

def print_deepest_path(graph: nx.DiGraph, root: str):
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

    deepest_path, _ = dfs(root, [], set())
    
    print("Deepest path:")
    for i, (source, relationship, target) in enumerate(deepest_path):
        print(f"{'  ' * i}- {source}")
        print(f"{'  ' * (i+1)}[{relationship}]")
    print(f"{'  ' * len(deepest_path)}- {deepest_path[-1][2]}")
