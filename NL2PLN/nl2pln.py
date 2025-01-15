import dspy
from .utils.prompts import NL2PLN_Signature

class NL2PLN(dspy.Module):
    def __init__(self, rag):
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)
        self.rag = rag

    def forward(self, sentence, previous_sentences=None):
        similar = self.rag.search_similar(sentence, limit=5)
        similar_examples = [f"Sentence: {item['sentence']}\nFrom Context:\n{'\n'.join(item.get('from_context', []))}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}" 
                       for item in similar if 'sentence' in item]

        return self.convert(sentence=sentence, similar=similar_examples, previous=previous_sentences)
