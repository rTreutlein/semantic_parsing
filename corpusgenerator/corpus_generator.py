import networkx as nx
from typing import List, Dict, Tuple

class CorpusGenerator:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.knowledge_graph = nx.DiGraph()

    def expand_sentence(self, sentence: str) -> List[str]:
        """
        Expand a sentence into related facts, rephrased versions, and new sentences for each edge type.
        """
        new_sentences = []
        edge_types = [
            "rephrases", "explains", "implies", "contrasts", "compares"
        ]

        prompts = {
            "rephrases": f"Rephrase this sentence in a simple way: '{sentence}'",
            "explains": f"Explain a part of this sentence further, starting with 'Because': '{sentence}'",
            "implies": f"What more general scenario does this imply? Start with 'Generally,': '{sentence}'",
            "contrasts": f"Provide a simple contrast to this: '{sentence}'",
            "compares": f"Compare this to something similar: '{sentence}'"
        }

        for edge_type, prompt in prompts.items():
            response = self.llm_client.generate(prompt)
            new_sentences.extend([s.strip() for s in response.split('\n') if s.strip()])

        return new_sentences

    def create_knowledge_graph(self, sentences: List[str]) -> nx.DiGraph:
        """
        Create a knowledge graph from the given sentences.
        """
        for sentence in sentences:
            self.knowledge_graph.add_node(sentence)

        edge_types = [
            "elaborates", "generalizes", "specifies", "contrasts", "compares",
            "causes", "results_from", "exemplifies", "defines"
        ]

        for i, sentence1 in enumerate(sentences):
            for j, sentence2 in enumerate(sentences[i+1:], start=i+1):
                prompt = f"Determine the relationship between these two sentences:\n1. {sentence1}\n2. {sentence2}\nChoose from: {', '.join(edge_types)}"
                relationship = self.llm_client.generate(prompt).strip().lower()
                
                if relationship in edge_types:
                    self.knowledge_graph.add_edge(sentence1, sentence2, relationship=relationship)

        return self.knowledge_graph

    def bootstrap_corpus(self, seed_sentence: str, iterations: int = 2) -> Tuple[List[str], nx.DiGraph]:
        """
        Run the corpus bootstrapping process for a given number of iterations.
        """
        all_sentences = [seed_sentence]
        
        for _ in range(iterations):
            # Expand the current seed sentence
            new_sentences = self.expand_sentence(seed_sentence)
            all_sentences.extend(new_sentences)
            
            # Create or update the knowledge graph
            self.create_knowledge_graph(all_sentences)
            
            # Update seed sentence for next iteration
            seed_sentence = new_sentences[-1]  # Use the last generated sentence as the new seed
        
        return all_sentences, self.knowledge_graph

# Example usage:
# llm_client = YourLLMClient()  # Replace with your actual LLM client
# generator = CorpusGenerator(llm_client)
# sentences, graph = generator.bootstrap_corpus("Coffee wakes people up.", iterations=2)
