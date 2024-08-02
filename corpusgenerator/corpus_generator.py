import networkx as nx
import random
import os
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import nltk
from nltk import word_tokenize, pos_tag

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
        "specializes": ("If a plant receives sunlight, it grows.", "A plant uses sunlight to generate carbohydrates."),
        "generalizes": ("If a dog is given a treat, it wags its tail.", "If an animal is rewarded, it shows signs of happiness."),
        "explains": ("If a dog is given a treat, it wags its tail.", "Giving a dog a treat makes it happy.\nHappy dogs wag their tail."),
        "complements": ("Regular exercise improves cardiovascular health.", "A balanced diet enhances overall physical well-being."),
        "negates": ("Studying hard leads to good grades.", "Procrastination often results in poor academic performance."),
    }

    REPHRASE_PROMPT = """
    Rephrase the following sentence to express the same meaning using different words.
    Output only the rephrased sentence, nothing else. Ensure the output is a single line.

    Original: {sentence}

    Rephrased sentence:
    """

    def __init__(self, llm_client, rephrase_model="meta-llama/llama-3.1-8b-instruct"):
        self.llm_client = llm_client
        self.knowledge_graph = nx.DiGraph()
        self.rephrase_model = rephrase_model
        self.word_counter = Counter()
        
        # Download necessary NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)

    def expand_rule(self, rule: str, debug: bool = False) -> List[Tuple[str, str]]:
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
        def rephrase_rule(rule_tuple):
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

    def bootstrap_corpus(self, initial_seed: str, iterations: int = 2, parallel_iterations: int = 1) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        
        :param initial_seed: The initial seed sentence to start the process.
        :param iterations: Total number of iterations to run.
        :param parallel_iterations: Number of iterations to run in parallel (default is 1, which means sequential processing).
        """
        all_rules = list(self.knowledge_graph.nodes())
        if not all_rules:
            all_rules = [initial_seed]
            self.knowledge_graph.add_node(initial_seed)
            self._update_word_counter(initial_seed)
        
            # First iteration (always sequential)
            print(f"\n--- Iteration 1 ---")
            seed_rule = initial_seed
            new_rules_with_relations = self.expand_rule(seed_rule)
            rephrased_rules = self.rephrase_rules(new_rules_with_relations)
            self._add_rules_to_graph(seed_rule, rephrased_rules, all_rules)
        else:
            print(f"\nUsing existing knowledge graph with {len(all_rules)} rules.")
            for rule in all_rules:
                self._update_word_counter(rule)

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
            else:
                # Sequential processing for single iterations
                iteration_rules = self._process_iteration(i)
                all_rules.extend(iteration_rules)

        return all_rules, self.knowledge_graph

    def _process_iteration(self, iteration: int, debug: bool = False) -> List[str]:
        print(f"\n--- Iteration {iteration} ---")
        seed_rule = self.select_seed_with_least_used_word()
        print(f"Selected seed rule: '{seed_rule}'")
        new_rules_with_relations = self.expand_rule(seed_rule, debug=debug)
        rephrased_rules = self.rephrase_rules(new_rules_with_relations, debug=debug)
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
            self._update_word_counter(new_rule)
        return new_rules

    def _update_word_counter(self, sentence: str):
        """
        Update the word counter with nouns from the given sentence.
        """
        tokens = word_tokenize(sentence)
        pos_tags = pos_tag(tokens)
        print(f"POS tags: {pos_tags}")
        nouns = [word.lower() for word, pos in pos_tags if pos.startswith('NN')]
        self.word_counter.update(nouns)

    def select_seed_with_least_used_word(self) -> str:
        """
        Select a node from the knowledge graph that contains one of the least used words.
        """
        if not self.knowledge_graph.nodes:
            raise ValueError("The knowledge graph is empty. Cannot select a seed.")
        
        min_count = min(self.word_counter.values())
        least_used_words = [word for word, count in self.word_counter.items() if count == min_count]
        least_used_word = random.choice(least_used_words)
        
        candidates = [node for node in self.knowledge_graph.nodes() if least_used_word in node.lower()]
        
        print(f"word_counter: {self.word_counter}")
        print(f"Least used words: {least_used_words}")
        print(f"Randomly selected least used word: '{least_used_word}'")
        print(f"Candidates: {candidates}")
        if candidates:
            return random.choice(candidates)
        else:
            return random.choice(list(self.knowledge_graph.nodes()))

    def save_knowledge_graph(self, filename: str):
        """
        Save the knowledge graph to a file in GraphML format.
        """
        nx.write_graphml(self.knowledge_graph, filename)

    def load_knowledge_graph(self, filename: str):
        """
        Load the knowledge graph from a file in GraphML format.
        """
        if os.path.exists(filename):
            self.knowledge_graph = nx.read_graphml(filename)
        else:
            print(f"File {filename} not found. Starting with an empty graph.")
            self.knowledge_graph = nx.DiGraph()
