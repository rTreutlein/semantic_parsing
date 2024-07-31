import networkx as nx
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
    """

    EXAMPLES = {
        "specializes": ("If a plant receives sunlight, it grows.", "If a tomato plant receives 6 hours of direct sunlight daily, it produces more fruit."),
        "generalizes": ("If a dog is given a treat, it wags its tail.", "If an animal is rewarded, it shows signs of happiness."),
        "complements": ("Regular exercise improves cardiovascular health.", "A balanced diet enhances overall physical well-being."),
        "negates": ("Studying hard leads to good grades.", "Procrastination often results in poor academic performance.")
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
            response = self.llm_client.generate(prompt)
            new_rules.extend([(r.strip(), edge_type) for r in response.split('\n') if r.strip()])

        return new_rules

    def bootstrap_corpus(self, seed_rule: str, iterations: int = 2) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        """
        all_rules = [seed_rule]
        self.knowledge_graph.add_node(seed_rule)
        
        for _ in range(iterations):
            # Expand the current seed rule
            new_rules_with_relations = self.expand_rule(seed_rule)
            
            for new_rule, relationship in new_rules_with_relations:
                all_rules.append(new_rule)
                self.knowledge_graph.add_node(new_rule)
                self.knowledge_graph.add_edge(seed_rule, new_rule, relationship=relationship)
            
            # Update seed rule for next iteration
            seed_rule = new_rules_with_relations[-1][0]  # Use the last generated rule as the new seed
        
        return all_rules, self.knowledge_graph

# Example usage:
# llm_client = YourLLMClient()  # Replace with your actual LLM client
# generator = CorpusGenerator(llm_client)
# sentences, graph = generator.bootstrap_corpus("Coffee wakes people up.", iterations=2)
