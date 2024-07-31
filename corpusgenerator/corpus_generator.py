import networkx as nx
from typing import List, Dict, Tuple

class CorpusGenerator:
    BASE_PROMPT = """
    You are an AI assistant tasked with generating simple, factual sentences related to a given input sentence.
    Your goal is to create new sentences that are clear, concise, and directly related to the input.
    Each new sentence should express a single, simple idea.
    Avoid complex language, jargon, or overly specific details.

    Input sentence: {sentence}
    Task: {task}

    Generate 1-3 simple sentences that {relationship} the input sentence.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.knowledge_graph = nx.DiGraph()

    def expand_sentence(self, sentence: str) -> List[Tuple[str, str]]:
        """
        Expand a sentence into related facts, rephrased versions, and new sentences for each edge type.
        Returns a list of tuples (new_sentence, relationship).
        """
        new_sentences = []

        prompts = {
            "rephrases": ("rephrase", "restate or paraphrase"),
            "explains": ("explain", "provide more detail or clarify"),
            "implies": ("imply", "suggest a more general scenario or consequence"),
            "contrasts": ("contrast with", "provide an opposite or contrasting idea to"),
            "compares": ("compare to", "draw a similarity or comparison with")
        }

        for edge_type, (task, relationship) in prompts.items():
            prompt = self.BASE_PROMPT.format(sentence=sentence, task=task, relationship=relationship)
            response = self.llm_client.generate(prompt)
            new_sentences.extend([(s.strip(), edge_type) for s in response.split('\n') if s.strip()])

        return new_sentences

    def bootstrap_corpus(self, seed_sentence: str, iterations: int = 2) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        """
        all_sentences = [seed_sentence]
        self.knowledge_graph.add_node(seed_sentence)
        
        for _ in range(iterations):
            # Expand the current seed sentence
            new_sentences_with_relations = self.expand_sentence(seed_sentence)
            
            for new_sentence, relationship in new_sentences_with_relations:
                all_sentences.append(new_sentence)
                self.knowledge_graph.add_node(new_sentence)
                self.knowledge_graph.add_edge(seed_sentence, new_sentence, relationship=relationship)
            
            # Update seed sentence for next iteration
            seed_sentence = new_sentences_with_relations[-1][0]  # Use the last generated sentence as the new seed
        
        return all_sentences, self.knowledge_graph

# Example usage:
# llm_client = YourLLMClient()  # Replace with your actual LLM client
# generator = CorpusGenerator(llm_client)
# sentences, graph = generator.bootstrap_corpus("Coffee wakes people up.", iterations=2)
