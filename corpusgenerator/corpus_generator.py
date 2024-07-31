import networkx as nx
import random
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    Now, generate 1-2 simple rules for the given input rule, focusing on the {relationship} relationship.
    Output only the new rules separated by newlines without any other text.
    """

    EXAMPLES = {
        "specializes": ("If a plant receives sunlight, it grows.", "If plant uses sunlight to generate carbohydrates."),
        "generalizes": ("If a dog is given a treat, it wags its tail.", "If an animal is rewarded, it shows signs of happiness."),
        "complements": ("Regular exercise improves cardiovascular health.", "A balanced diet enhances overall physical well-being."),
        "negates": ("Studying hard leads to good grades.", "Procrastination often results in poor academic performance."),
    }

    REPHRASE_PROMPT = """
    Rephrase the following sentence to express the same meaning using different words:

    Original: {sentence}

    Rephrased:
    """

    def __init__(self, llm_client, rephrase_model="meta-llama/llama-3.1-8b-instruct"):
        self.llm_client = llm_client
        self.knowledge_graph = nx.DiGraph()
        self.rephrase_model = rephrase_model

    def expand_rule(self, rule: str) -> List[Tuple[str, str]]:
        """
        Expand a rule into related rules for each edge type.
        Returns a list of tuples (new_rule, relationship).
        """
        def expand_for_edge_type(edge_type):
            example_input, example_output = self.EXAMPLES[edge_type]
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
            return [(r.strip(), edge_type) for r in response.split('\n') if r.strip()]

        new_rules = []
        with ThreadPoolExecutor() as executor:
            future_to_edge_type = {executor.submit(expand_for_edge_type, edge_type): edge_type for edge_type in self.EXAMPLES}
            for future in as_completed(future_to_edge_type):
                new_rules.extend(future.result())

        return new_rules

    def rephrase_rules(self, rules: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        Rephrase the given rules using a different LLM model.
        """
        def rephrase_rule(rule_tuple):
            rule, relationship = rule_tuple
            prompt = self.REPHRASE_PROMPT.format(sentence=rule)
            print(f"\nRephrasing rule: '{rule}'")
            print(f"Prompt: {prompt}")
            response = self.llm_client.generate(prompt, model=self.rephrase_model)
            print(f"Rephrased: {response}")
            return (response, relationship)

        rephrased_rules = rules.copy()
        with ThreadPoolExecutor() as executor:
            future_to_rule = {executor.submit(rephrase_rule, rule_tuple): rule_tuple for rule_tuple in rules}
            for future in as_completed(future_to_rule):
                rephrased_rules.append(future.result())
        return rephrased_rules

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
            
            # Rephrase the new rules also returns the original rules
            rephrased_rules = self.rephrase_rules(new_rules_with_relations)
            
            print("\nNew rules generated and rephrased:")
            for new_rule, relationship in rephrased_rules:
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
