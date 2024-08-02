import networkx as nx
import random
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy.spatial.distance import cosine
import embedder
from collections import defaultdict
from llm_client import OpenAIClient

class CorpusGenerator:
    BASE_PROMPT = """
    You are an AI assistant tasked with generating simple, factual sentences that express logical relationships or rules.
    Your goal is to create new sentences that are clear, concise, and directly related to the input rule.
    Each new sentence should express a single, simple logical relationship that can be translated into predicate logic.
    Avoid complex language, jargon, or overly specific details.

    Input rule: {sentence}
    Task: Generate a new rule that {relationship} the input rule.

    Examples:
    {examples}

    Now, generate 1-2 simple rules for the given input rule, focusing on the {relationship} relationship.
    Output only the new rules separated by newlines without any other text.
    """

    EXAMPLES = {
        "specializes": [
            ("If a plant receives sunlight, it grows.", "A plant uses sunlight to generate carbohydrates."),
            ("Water is essential for life.", "H2O molecules are crucial for cellular functions."),
            ("Exercise improves health.", "Cardiovascular exercise strengthens the heart muscle."),
        ],
        "generalizes": [
            ("If a dog is given a treat, it wags its tail.", "If an animal is rewarded, it shows signs of happiness."),
            ("Apples are rich in fiber.", "Many fruits contain beneficial dietary fiber."),
            ("Cats purr when content.", "Animals often display specific behaviors when they're happy."),
        ],
        "explains": [
            ("If a dog is given a treat, it wags its tail.", "Giving a dog a treat makes it happy.\nHappy dogs wag their tail."),
            ("The sky appears blue.", "Sunlight scatters in the atmosphere.\nBlue light scatters more than other colors."),
            ("Plants grow towards light.", "Plants contain photoreceptors.\nPhotoreceptors detect light direction."),
        ],
        "complements": [
            ("Regular exercise improves cardiovascular health.", "A balanced diet enhances overall physical well-being."),
            ("Reading enhances vocabulary.", "Writing practice improves language skills."),
            ("Adequate sleep boosts immune function.", "Stress management techniques support mental health."),
        ],
        "negates": [
            ("Studying hard leads to good grades.", "Procrastination often results in poor academic performance."),
            ("Regular exercise promotes health.", "A sedentary lifestyle can lead to various health issues."),
            ("Saving money contributes to financial stability.", "Overspending can result in financial stress."),
        ],
    }

    REPHRASE_PROMPT = """
    Rephrase the following sentence to express the same meaning using different words.
    Output only the rephrased sentence, nothing else. Ensure the output is a single line.

    Original: {sentence}

    Rephrased sentence:
    """

    def __init__(self, llm_client: OpenAIClient, rephrase_model: str = "meta-llama/llama-3.1-8b-instruct"):
        self.llm_client: OpenAIClient = llm_client
        self.knowledge_graph: nx.DiGraph = nx.DiGraph()
        self.rephrase_model: str = rephrase_model
        self.embeddings: Dict[str, Optional[np.ndarray]] = defaultdict(lambda: None)

    def expand_rule(self, rule: str, debug: bool = False) -> List[Tuple[str, str]]:
        """
        Expand a rule into related rules for each edge type.
        Returns a list of tuples (new_rule, relationship).
        """
        def expand_for_edge_type(edge_type):
            examples = "\n".join([f"Input rule: {input}\nOutput: {output}" for input, output in self.EXAMPLES[edge_type]])
            prompt = self.BASE_PROMPT.format(
                sentence=rule,
                relationship=edge_type,
                examples=examples
            )
            response = self.llm_client.generate(prompt)
            return (edge_type, prompt, response, [(r.strip(), edge_type) for r in response.split('\n') if r.strip()])

        new_rules = []
        output = []
        with ThreadPoolExecutor() as executor:
            future_to_edge_type = {executor.submit(expand_for_edge_type, edge_type): edge_type for edge_type in self.EXAMPLES}
            for future in as_completed(future_to_edge_type):
                edge_type, prompt, response, rules = future.result()
                if debug:
                    output.append(f"\nExpanding rule: '{rule}' with relationship: '{edge_type}'")
                    output.append(f"Prompt: {prompt}")
                    output.append(f"Response: {response}")
                new_rules.extend(rules)

        if debug:
            print("\n".join(output))
        return new_rules

    def rephrase_rules(self, rules: List[Tuple[str, str]], debug: bool = False) -> List[Tuple[str, str]]:
        """
        Rephrase the given rules using a different LLM model.
        """
        def rephrase_rule(rule_tuple: Tuple[str, str]) -> Tuple[str, str, str, str]:
            rule, relationship = rule_tuple
            prompt = self.REPHRASE_PROMPT.format(sentence=rule)
            response = self.llm_client.generate(prompt, model=self.rephrase_model)
            return (rule, prompt, response, relationship)

        rephrased_rules = rules.copy()
        output = []
        with ThreadPoolExecutor() as executor:
            future_to_rule = {executor.submit(rephrase_rule, rule_tuple): rule_tuple for rule_tuple in rules}
            for future in as_completed(future_to_rule):
                rule, prompt, response, relationship = future.result()
                if debug:
                    output.append(f"\nRephrasing rule: '{rule}'")
                    output.append(f"Prompt: {prompt}")
                if '\n' not in response:
                    if debug:
                        output.append(f"Rephrased: {response}")
                    rephrased_rules.append((response, relationship))
                elif debug:
                    output.append(f"Skipped: Response contains multiple lines")

        if debug:
            print("\n".join(output))
        return rephrased_rules

    def bootstrap_corpus(self, initial_seeds: List[str], iterations: int = 2, parallel_iterations: int = 1) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        
        :param initial_seeds: The initial seed sentences to start the process.
        :param iterations: Total number of iterations to run.
        :param parallel_iterations: Number of iterations to run in parallel (default is 1, which means sequential processing).
        :return: A tuple containing the list of all rules and the knowledge graph.
        """
        all_rules = list(self.knowledge_graph.nodes())
        if not all_rules:
            all_rules = initial_seeds.copy()
            for seed in initial_seeds:
                self.knowledge_graph.add_node(seed)
        
            # First iteration (always sequential)
            print(f"\n--- Iteration 1 ---")
            for seed_rule in initial_seeds:
                print(f"Processing seed: '{seed_rule}'")
                new_rules_with_relations = self.expand_rule(seed_rule, debug=True)
                rephrased_rules = self.rephrase_rules(new_rules_with_relations, debug=True)
                self._add_rules_to_graph(seed_rule, rephrased_rules, all_rules)
        else:
            print(f"\nUsing existing knowledge graph with {len(all_rules)} rules.")

        # Calculate embeddings for all rules
        self._update_embeddings(all_rules)

        # Subsequent iterations
        for i in range(2, iterations + 1, parallel_iterations):
            batch_size = min(parallel_iterations, iterations - i + 1)
            if batch_size > 1:
                # Parallel processing for batches
                with ThreadPoolExecutor() as executor:
                    future_to_iteration = {executor.submit(self._process_iteration, j): j for j in range(i, i + batch_size)}
                    for future in as_completed(future_to_iteration):
                        iteration_rules = future.result()
                        all_rules.extend(iteration_rules)
                        self._update_embeddings(iteration_rules)
            else:
                # Sequential processing for single iterations
                iteration_rules = self._process_iteration(i)
                all_rules.extend(iteration_rules)
                self._update_embeddings(iteration_rules)

        return all_rules, self.knowledge_graph

    def _process_iteration(self, iteration: int, debug: bool = False) -> List[str]:
        print(f"\n--- Iteration {iteration} ---")
        seed_rule: str = self.select_most_novel_rule()
        print(f"Selected seed rule: '{seed_rule}'")
        new_rules_with_relations: List[Tuple[str, str]] = self.expand_rule(seed_rule, debug=debug)
        rephrased_rules: List[Tuple[str, str]] = self.rephrase_rules(new_rules_with_relations, debug=debug)
        return self._add_rules_to_graph(seed_rule, rephrased_rules, [], debug=debug)

    def _add_rules_to_graph(self, seed_rule: str, rephrased_rules: List[Tuple[str, str]], all_rules: List[str], debug: bool = False) -> List[str]:
        new_rules = []
        if debug:
            print("\nNew rules generated and rephrased:")
        for new_rule, relationship in rephrased_rules:
            all_rules.append(new_rule)
            new_rules.append(new_rule)
            self.knowledge_graph.add_node(new_rule)
            self.knowledge_graph.add_edge(seed_rule, new_rule, relationship=relationship)
            if debug:
                print(f"- '{new_rule}' (Relationship: {relationship})")
        return new_rules

    def select_most_novel_rule(self) -> str:
        """
        Select a rule from the knowledge graph based on vector embeddings,
        using the distance as a weight for sampling.
        """
        if not self.knowledge_graph.nodes:
            raise ValueError("The knowledge graph is empty. Cannot select a seed.")
        
        all_rules: List[str] = list(self.knowledge_graph.nodes())
        embeddings: List[np.ndarray] = [self.embeddings[rule] for rule in all_rules]
        
        # Calculate the average embedding
        avg_embedding: np.ndarray = np.mean(embeddings, axis=0)
        
        # Calculate the cosine distance between each rule's embedding and the average embedding
        distances: List[float] = [cosine(embedding, avg_embedding) for embedding in embeddings]
        
        # Normalize distances to use as weights
        weights: np.ndarray = np.array(distances) / np.sum(distances)
        
        # Sample a rule based on the weights
        selected_rule: str = random.choices(all_rules, weights=weights, k=1)[0]
        
        print(f"Selected rule: '{selected_rule}'\n")
        return selected_rule

    def _update_embeddings(self, rules: List[str]) -> None:
        """
        Update the embeddings for the given rules.
        """
        new_rules = [rule for rule in rules if self.embeddings[rule] is None]
        if new_rules:
            new_embeddings = embedder.embed_sentences(new_rules)
            for rule, embedding in zip(new_rules, new_embeddings):
                self.embeddings[rule] = embedding

    def save_knowledge_graph(self, filename: str) -> None:
        """
        Save the knowledge graph to a file in GraphML format.
        """
        nx.write_graphml(self.knowledge_graph, filename)

    def load_knowledge_graph(self, filename: str) -> None:
        """
        Load the knowledge graph from a file in GraphML format.
        """
        if os.path.exists(filename):
            self.knowledge_graph = nx.read_graphml(filename)
        else:
            print(f"File {filename} not found. Starting with an empty graph.")
            self.knowledge_graph = nx.DiGraph()
