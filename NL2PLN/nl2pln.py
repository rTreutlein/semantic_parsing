import dspy
from .utils.prompts import NL2PLN_Signature
from .utils.cleanPLN import cleanPLN

class NL2PLN(dspy.Module):
    def __init__(self, rag):
        self.convert = dspy.ChainOfThought(NL2PLN_Signature)
        self.rag = rag

    def forward(self, sentences, previous_sentences=None, n=1):
        if n > 1:
            raise NotImplementedError("Only n=1 is supported")
        # Handle single sentence case
        if isinstance(sentences, str):
            sentences = [sentences]
            
        # Collect similar examples for each sentence in separate lists
        all_examples = []
        for sentence in sentences:
            similar = self.rag.search_similar(sentence, limit=3)
            examples = []
            for item in similar:
                if 'sentence' not in item:
                    continue
                    
                example = []
                example.append(f"Sentence: {item['sentence']}")
                
                if item.get('from_context'):
                    example.append("From Context:")
                    example.extend(f"  {ctx}" for ctx in item['from_context'])
                    
                if item.get('type_definitions'):
                    example.append("Type Definitions:")
                    example.extend(f"  {typedef}" for typedef in item['type_definitions'])
                    
                if item.get('statements'):
                    example.append("Statements:")
                    example.extend(f"  {stmt}" for stmt in item['statements'])
                    
                examples.append('\n'.join(example))
            all_examples.append(examples)
            
        # Interleave examples from each sentence's similar results
        selected_examples = []
        seen = set()
        max_examples = max(len(examples) for examples in all_examples)
        
        # Take examples in order: first example from each sentence, then second, etc.
        for i in range(max_examples):
            for sentence_examples in all_examples:
                if i < len(sentence_examples) and sentence_examples[i] not in seen:
                    selected_examples.append(sentence_examples[i])
                    seen.add(sentence_examples[i])
                    
        # Ensure we have at least max(5, len(sentences)) examples if available
        target_count = max(5, len(sentences))
        selected_examples = selected_examples[:target_count]

        # Process as a batch with context
        joined_sentences = "\n".join([f"- {s}" for s in sentences])
        res = self.convert(
            sentences=joined_sentences,
            similar=selected_examples,
            previous=previous_sentences,
        )

        # Post-process all outputs
        res.context = [cleanPLN(x) for x in res.context]
        res.typedefs = [cleanPLN(x) for x in res.typedefs]
        res.statements = [cleanPLN(x) for x in res.statements]
        res.questions = [cleanPLN(x) for x in res.questions]
        
        return res
