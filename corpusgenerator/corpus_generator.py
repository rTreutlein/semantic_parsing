import networkx as nx
import random
from typing import List, Dict, Tuple

class CorpusGenerator:
    BASE_PROMPT = """
    You are an AI assistant tasked with generating simple, factual sentences that express logical relationships or rules.
    Your goal is to create new sentences that are clear, concise, and directly related to the input rule.
    Each new sentence should express a single, simple logical relationship that can be translated into predicate logic.
    Avoid complex language, jargon, or overly specific details.

    Input rule: {sentence}
    Task: Generate a new rule that {relationship} the input rule.

    Example:
    Input rule: {example_input}
    Output: {example_output}

    Now, generate 1-3 simple rules for the given input rule, focusing on the {relationship} relationship.
    Output only the new rules separated by newlines without any other text.
    """

    EXAMPLES = {
        "specializes": ("If a plant receives sunlight, it grows.", "If a tomato plant receives 6 hours of direct sunlight daily, it produces more fruit."),
        "generalizes": ("If a dog is given a treat, it wags its tail.", "If an animal is rewarded, it shows signs of happiness."),
        "complements": ("Regular exercise improves cardiovascular health.", "A balanced diet enhances overall physical well-being."),
        "negates": ("Studying hard leads to good grades.", "Procrastination often results in poor academic performance."),
        "rephrase": ("Coffee wakes people up.", "Consuming coffee increases alertness in individuals.")
    }

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.knowledge_graph = nx.DiGraph()

    def expand_rule(self, rule: str) -> List[Tuple[str, str]]:
        """
        Expand a rule into related rules for each edge type.
        Returns a list of tuples (new_rule, relationship).
        """
        new_rules = []

        for edge_type, (example_input, example_output) in self.EXAMPLES.items():
            prompt = self.BASE_PROMPT.format(
                sentence=rule,
                relationship=edge_type,
                example_input=example_input,
                example_output=example_output
            )
            print(f"\nExpanding rule: '{rule}' with relationship: '{edge_type}'")
            print(f"Prompt: {prompt}")
            response = self.llm_client.generate(prompt)
            print(f"Response: {response}")
            new_rules.extend([(r.strip(), edge_type) for r in response.split('\n') if r.strip()])

        return new_rules

    def bootstrap_corpus(self, initial_seed: str, iterations: int = 2) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        """
        all_rules = [initial_seed]
        self.knowledge_graph.add_node(initial_seed)
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1} ---")
            # Select a random seed for this iteration
            seed_rule = self.select_random_seed()
            print(f"Selected seed rule: '{seed_rule}'")
            
            # Expand the current seed rule
            new_rules_with_relations = self.expand_rule(seed_rule)
            
            print("\nNew rules generated:")
            for new_rule, relationship in new_rules_with_relations:
                all_rules.append(new_rule)
                self.knowledge_graph.add_node(new_rule)
                self.knowledge_graph.add_edge(seed_rule, new_rule, relationship=relationship)
                print(f"- '{new_rule}' (Relationship: {relationship})")
        
        return all_rules, self.knowledge_graph

    def select_random_seed(self) -> str:
        """
        Randomly select a node from the knowledge graph to use as the next seed phrase.
        """
        if not self.knowledge_graph.nodes:
            raise ValueError("The knowledge graph is empty. Cannot select a random seed.")
        return random.choice(list(self.knowledge_graph.nodes))

# Example usage:
# llm_client = YourLLMClient()  # Replace with your actual LLM client
# generator = CorpusGenerator(llm_client)
# sentences, graph = generator.bootstrap_corpus("Coffee wakes people up.", iterations=2)
# next_seed = generator.select_random_seed()
