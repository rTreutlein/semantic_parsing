import networkx as nx
import random
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy.spatial.distance import cosine
import utils.embedder as embedder
from collections import defaultdict
from utils.llm_client import OpenAIClient
from utils.examples import EXAMPLES

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

    def __init__(self, llm_client: OpenAIClient, rephrase_model: str = "meta-llama/llama-3.1-8b-instruct"):
        self.llm_client: OpenAIClient = llm_client
        self.knowledge_graph: nx.DiGraph = nx.DiGraph()
        self.rephrase_model: str = rephrase_model
        self.embeddings: Dict[str, Optional[np.ndarray]] = defaultdict(lambda: None)

    def _get_connected_edge_types(self, rule: str) -> Dict[str, int]:
        """
        Get the outgoing edge types connected to the given rule in the knowledge graph,
        along with their frequencies.
        """
        connected_edges = self.knowledge_graph.out_edges(rule, data=True)
        edge_type_counts = {}
        for _, _, edge in connected_edges:
            edge_type = edge['relationship']
            edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
        return edge_type_counts

    def expand_rule(self, rule: str, debug: bool = False) -> List[Tuple[str, str]]:
        """
        Expand a rule into related rules for one edge type, chosen based on inverse probability
        of existing connections. Returns a list of tuples (new_rule, relationship).
        """
        connected_edge_types = self._get_connected_edge_types(rule)
        all_edge_types = set(EXAMPLES.keys())
        
        # Calculate weights for edge type selection
        weights = []
        edge_types = []
        for edge_type in all_edge_types:
            if edge_type in connected_edge_types:
                weight = 1 / connected_edge_types[edge_type]
            else:
                weight = 1  # Highest weight for non-existing edge types
            weights.append(weight)
            edge_types.append(edge_type)
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Choose an edge type based on the calculated weights
        edge_type = random.choices(edge_types, weights=normalized_weights, k=1)[0]

        examples = "\n".join([f"Input rule: {input}\nOutput: {output}" for input, output in EXAMPLES[edge_type]])
        prompt = self.BASE_PROMPT.format(
            sentence=rule,
            relationship=edge_type,
            examples=examples
        )
        response = self.llm_client.generate(prompt)
        new_rules = [(r.strip(), edge_type) for r in response.split('\n') if r.strip()]

        if debug:
            print(f"\nExpanding rule: '{rule}' with relationship: '{edge_type}'")
            print(f"Prompt: {prompt}")
            print(f"Response: {response}")

        return new_rules

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
        else:
            print(f"\nUsing existing knowledge graph with {len(all_rules)} rules.")

        # Calculate embeddings for all rules
        self._update_embeddings(all_rules)

        # Iterations
        for i in range(0, iterations, parallel_iterations):
            batch_size = min(parallel_iterations, iterations - i)
            if batch_size > 1:
                # Parallel processing for batches
                tmp_iter_ruels = []
                with ThreadPoolExecutor() as executor:
                    future_to_iteration = {executor.submit(self._process_iteration, j): j for j in range(i, i + batch_size)}
                    for future in as_completed(future_to_iteration):
                        iteration_rules = future.result()
                        tmp_iter_ruels.extend(iteration_rules)
                        all_rules.extend(iteration_rules)
                self._update_embeddings(tmp_iter_ruels)
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
        new_rules: List[Tuple[str, str]] = self.expand_rule(seed_rule, debug=debug)
        return self._add_rules_to_graph(seed_rule, new_rules, [], debug=debug)

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
        if len(all_rules) == 1:
            return all_rules[0]
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
