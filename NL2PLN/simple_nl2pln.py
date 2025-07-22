import dspy
import concurrent.futures
from .utils.prompts import NL2PLN_Signature
from .utils.cleanPLN import cleanPLN

class SimpleNL2PLN(dspy.Module):
    def __init__(self):
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)

    def forward(self, sentences, previous_sentences=None):
        # Handle single sentence case
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # No RAG - use empty examples
        selected_examples = []

        # Process as a batch with context
        joined_sentences = "\n".join([f"- {s}" for s in sentences])

        #print("----------------------------------------------")
        #print("Input:")
        #print(joined_sentences)
        #print("No RAG examples (simplified version)")
        #print(previous_sentences)
        #print("----------------------------------------------")

        #with dspy.context(lm=dspy.LM('openrouter/anthropic/claude-sonnet-4', temperature=1, cache=False)):
        with dspy.context(lm=dspy.LM('openai/gpt-4o', temperature=1, cache=False)):

            res = self.convert(
                sentences=joined_sentences,
                similar=selected_examples,
                previous=previous_sentences,
            )
            res.statements = [cleanPLN(x) for x in res.statements]
            res.questions = [cleanPLN(x) for x in res.questions]
            return res
