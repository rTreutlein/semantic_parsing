import os
from llm_client import OpenAIClient
from corpus_generator import CorpusGenerator

def main():
    # Get OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")

    # Initialize OpenAI client
    llm_client = OpenAIClient(api_key)

    # Initialize CorpusGenerator
    generator = CorpusGenerator(llm_client)

    # Start the corpus generation process
    initial_seed = "Coffee wakes people up."
    iterations = 3
    sentences, graph = generator.bootstrap_corpus(initial_seed, iterations)

    # Print the generated sentences
    print("\nGenerated sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")

    # Print some basic information about the knowledge graph
    print(f"\nKnowledge Graph:")
    print(f"Number of nodes: {graph.number_of_nodes()}")
    print(f"Number of edges: {graph.number_of_edges()}")

    # Print detailed graph information
    print("\nDetailed Graph Information:")
    for node in graph.nodes():
        print(f"\nNode: '{node}'")
        for neighbor in graph.neighbors(node):
            edge_data = graph.get_edge_data(node, neighbor)
            print(f"  -> '{neighbor}' (Relationship: {edge_data['relationship']})")

if __name__ == "__main__":
    main()
