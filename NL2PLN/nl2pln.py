import dspy
from .utils.prompts import NL2PLN_Signature

class NL2PLN(dspy.Module):
    def __init__(self, rag):
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)
        self.rag = rag

    @staticmethod
    def balance_parentheses(expr: str) -> str:
        """Balance parentheses in an expression by adding or removing at the end."""
        # Add opening parenthesis if expression starts with colon
        if expr.startswith(':'):
            expr = '(' + expr
            
        open_count = expr.count('(')
        close_count = expr.count(')')
        
        if open_count > close_count:
            # Add missing closing parentheses
            return expr + ')' * (open_count - close_count)
        elif close_count > open_count:
            # Remove only excess closing parentheses from the end
            excess = close_count - open_count
            i = len(expr) - 1
            
            # First verify the end of string contains only closing parentheses
            while i >= 0 and excess > 0:
                if expr[i] != ')':
                    # Found non-parenthesis - give up and return original
                    return expr
                i -= 1
                excess -= 1
                
            # If we got here, we found enough closing parentheses at the end
            # Now remove the exact number of excess ones
            excess = close_count - open_count
            return expr[:-excess]
        return expr
 

    def forward(self, sentences, previous_sentences=None, n=1):
        # Handle single sentence case
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # Aggregate similar examples from all sentences
        similar_examples = []
        for sentence in sentences:
            similar = self.rag.search_similar(sentence, limit=3)
            similar_examples.extend([
                f"Sentence: {item['sentence']}\nFrom Context:\n{'\n'.join(item.get('from_context', []))}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}"
                for item in similar if 'sentence' in item
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_examples = [
            ex for ex in similar_examples
            if not (ex in seen or seen.add(ex))
        ]

        # Process as a batch with context
        joined_sentences = "\n".join([f"- {s}" for s in sentences])
        res = self.convert(
            sentences=joined_sentences,
            similar=unique_examples[:5],  # Take top 5 unique examples
            previous=previous_sentences,
            n=n
        )

        # Post-process all outputs
        res.context = [self.balance_parentheses(x) for x in res.context]
        res.typedefs = [self.balance_parentheses(x) for x in res.typedefs]
        res.statements = [self.balance_parentheses(x) for x in res.statements]
        
        return res
