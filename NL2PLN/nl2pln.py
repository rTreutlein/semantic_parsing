import dspy
from .utils.prompts import NL2PLN_Signature
from .utils.cache_handler import CacheHandler

class NL2PLN(dspy.Module):
    def __init__(self, rag, cache_file: str = "nl2pln_cache.json"):
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)
        self.rag = rag
        self.cache = CacheHandler(cache_file)

    def forward(self, sentence, previous_sentences=None):
        # Create a cache key from the input
        cache_key = str({
            "sentence": sentence,
            "previous_sentences": previous_sentences
        })
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        similar = self.rag.search_similar(sentence, limit=5)
        similar_examples = [f"Sentence: {item['sentence']}\nFrom Context:\n{'\n'.join(item.get('from_context', []))}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}" 
                       for item in similar if 'sentence' in item]

        prediction = self.convert(sentence=sentence, similar=similar_examples, previous=previous_sentences)
        
        # Cache the result before returning
        self.cache.set(cache_key, prediction)
        return prediction
