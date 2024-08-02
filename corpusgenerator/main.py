import os
from typing import List
from llm_client import OpenAIClient
from corpus_generator import CorpusGenerator
from utils import print_tree, print_deepest_path
import networkx as nx

def main() -> None:
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
    graph_file: str = "knowledge_graph.graphml"
    if os.path.exists(graph_file):
        print(f"Loading existing knowledge graph from {graph_file}")
        generator.load_knowledge_graph(graph_file)
    else:
        print("No existing knowledge graph found. Starting with an empty graph.")

    # Start the corpus generation process
    initial_seeds: List[str] = [
        "If an object is dropped, it will fall to the ground.",
        "When the sun sets, it gets darker outside.",
        "Water freezes at 0 degrees Celsius.",
        "Plants need sunlight and water to grow.",
        "Fire requires oxygen to burn.",
        "Objects cast shadows when light shines on them."
    ]
    iterations: int = 10
    parallel_iterations: int = 3  # Run 3 iterations in parallel after the first iteration
    sentences: List[str]
    graph: nx.DiGraph
    sentences, graph = generator.bootstrap_corpus(initial_seeds, iterations, parallel_iterations)

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
    print_tree(graph, initial_seeds)

    # Print the deepest path in the knowledge graph
    print("\nDeepest Path in the Knowledge Graph:")
    print_deepest_path(graph, initial_seeds)

if __name__ == "__main__":
    main()
