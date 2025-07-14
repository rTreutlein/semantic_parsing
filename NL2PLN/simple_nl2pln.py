import dspy
import concurrent.futures
from .utils.prompts import NL2PLN_Signature
from .utils.cleanPLN import cleanPLN

class SimpleNL2PLN(dspy.Module):
    def __init__(self,n):
        print("SimpleNL2PLN n:")
        #print(n)
        self.n = n
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)
        optimized = dspy.load("nl2pln")
        if optimized:
            self.convert.predict.demos = optimized.predict.demos
            self.convert.predict.signature.instructions = optimized.predict.signature.instructions
            print(optimized.predict.signature.instructions)
        else:
            print("Failed to load optimized")
            exit()

    def forward(self, sentences, previous_sentences=None):
        # Handle single sentence case
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # No RAG - use empty examples
        selected_examples = []

        # Process as a batch with context
        joined_sentences = "\n".join([f"- {s}" for s in sentences])

        print("----------------------------------------------")
        print("Input:")
        print(joined_sentences)
        print("No RAG examples (simplified version)")
        print(previous_sentences)
        print("----------------------------------------------")


        def _convert_worker(_):
            with dspy.context(lm=dspy.LM('openrouter/anthropic/claude-sonnet-4', temperature=1, cache=False)):
                res = self.convert(
                    sentences=joined_sentences,
                    similar=selected_examples,
                    previous=previous_sentences,
                )
                res.statements = [cleanPLN(x) for x in res.statements]
                res.questions = [cleanPLN(x) for x in res.questions]
                return res

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.n) as executor:
            futures = [executor.submit(_convert_worker, i) for i in range(self.n)]
            reslist = [f.result() for f in futures]

        return reslist
