import os
from llm_client import OpenAIClient
from corpus_generator import CorpusGenerator

def print_tree(graph, node, level=0, visited=None):
    if visited is None:
        visited = set()
    
    if node in visited:
        return
    visited.add(node)
    
    print("  " * level + f"- {node}")
    for neighbor in graph.neighbors(node):
        edge_data = graph.get_edge_data(node, neighbor)
        print("  " * (level + 1) + f"[{edge_data['relationship']}]")
        print_tree(graph, neighbor, level + 2, visited)

def main():
    # Get OpenAI API key from environment variable
    base_url = "https://openrouter.ai/api/v1"
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("Please set the OPENROUTER_API_KEY environment variable.")

    # Initialize OpenAI client
    llm_client = OpenAIClient(api_key, base_url=base_url)

    # Initialize CorpusGenerator
    generator = CorpusGenerator(llm_client)

    # Check if a saved graph exists
    graph_file = "knowledge_graph.graphml"
    if os.path.exists(graph_file):
        print(f"Loading existing knowledge graph from {graph_file}")
        generator.load_knowledge_graph(graph_file)
    else:
        print("No existing knowledge graph found. Starting with an empty graph.")

    # Start the corpus generation process
    initial_seed = "Coffee wakes people up."
    iterations = 10
    parallel_iterations = 3  # Run 3 iterations in parallel after the first iteration
    sentences, graph = generator.bootstrap_corpus(initial_seed, iterations, parallel_iterations)

    # Save the updated knowledge graph
    generator.save_knowledge_graph(graph_file)
    print(f"Knowledge graph saved to {graph_file}")

    # Print the generated sentences
    print("\nGenerated sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")

    # Print some basic information about the knowledge graph
    print(f"\nKnowledge Graph:")
    print(f"Number of nodes: {graph.number_of_nodes()}")
    print(f"Number of edges: {graph.number_of_edges()}")

    # Print the knowledge graph as a tree
    print("\nKnowledge Graph Tree Structure:")
    print_tree(graph, initial_seed)

if __name__ == "__main__":
    main()
