import dspy
from typing import List, Dict, Tuple, Optional
from hyperon import MeTTa
from NL2PLN.nl2pln import NL2PLN
from .ragclass import RAG

class SimilarSentencesSignature(dspy.Signature):
    """Generate semantically similar sentences to the input."""
    original_sentence: str = dspy.InputField()
    similar_sentences: List[str] = dspy.OutputField()

class QuestionAnswerSignature(dspy.Signature):
    """Generate question-answer pairs that can be answered using the input sentence."""
    sentence: str = dspy.InputField()
    qa_pairs: List[Dict[str, str]] = dspy.OutputField()

class SentenceAnalyzer(dspy.Module):
    """Enhanced NL2PLN module that validates conversions through Q&A consistency"""
    
    def __init__(self, rag: Optional[RAG] = None):
        super().__init__()
        self.generate_similar = dspy.ChainOfThought(SimilarSentencesSignature)
        self.generate_qa = dspy.ChainOfThought(QuestionAnswerSignature)
        self.nl2pln = NL2PLN(rag if rag else RAG())
        
    def forward(self, sentence: str, previous_sentences: Optional[List[str]] = None) -> Dict:
        """
        Run the full analysis pipeline using NL2PLN for conversions.
        Matches the NL2PLN interface with additional validation.
        
        Args:
            sentence: Input sentence to convert
            previous_sentences: Optional list of previous sentences for context
            
        Returns:
            Dict containing validated PLN conversion with type definitions and statements
        """
        # Generate similar sentences
        similar = self.generate_similar(original_sentence=sentence)
        all_sentences = [sentence] + similar.similar_sentences
        
        # Convert each sentence using NL2PLN with multiple completions
        pln_conversions = []
        for sent in all_sentences:
            print(f"\nProcessing sentence: {sent}")
            pln_data = self.nl2pln.forward(sent, previous_sentences, n=3)
            print(f"PLN data: {pln_data}")
            print(f"PLN data type: {type(pln_data)}")
            if hasattr(pln_data, 'completions'):
                print(f"Number of completions: {len(pln_data.completions)}")
                for completion in pln_data.completions:
                    print(f"Completion: {completion}")
                    pln_conversions.append({
                        "sentence": sent,
                        "typedefs": completion.typedefs,
                        "statements": completion.statements,
                        "context": completion.context
                    })
            else:
                print("No completions attribute found")
                pln_conversions.append({
                    "sentence": sent,
                    "typedefs": pln_data.typedefs,
                    "statements": pln_data.statements,
                    "context": pln_data.context
                })
                
        # Generate Q&A pairs for each sentence
        qa_pairs = []
        for sent in all_sentences:
            qa = self.generate_qa(sentence=sent)
            qa_pairs.extend(qa.qa_pairs)
            
        # Convert Q&A pairs using NL2PLN
        qa_conversions = []
        for qa in qa_pairs:
            q_conv = self.nl2pln.forward(qa["question"], previous_sentences)
            a_conv = self.nl2pln.forward(qa["answer"], previous_sentences)
            qa_conversions.append({
                "original": qa,
                "question_conv": q_conv,
                "answer_conv": a_conv
            })
            
        # Validate through inference
        results = self._validate_inference(pln_conversions, qa_conversions)
        
        # Score and select best conversion
        best_conversion, score = self._score_conversions(results)
        
        # Return in same format as NL2PLN with additional validation info
        return {
            "typedefs": best_conversion["typedefs"],
            "statements": best_conversion["statements"],
            "context": best_conversion["context"],
            "validation_score": score,
            "validation_results": results
        }
        
    def _validate_inference(self, pln_conversions: List[Dict], 
                          qa_conversions: List[Dict]) -> List[Dict]:
        """Run inference validation for each PLN conversion"""
        results = []
        
        for conv in pln_conversions:
            # Create a temporary MeTTa handler for validation
            metta = MeTTaHandler("temp_kb.metta", read_only=True)
            
            # Add type definitions and statements
            try:
                for typedef in conv["typedefs"]:
                    metta.add_to_context(typedef)
                for stmt in conv["statements"]:
                    metta.add_to_context(stmt)
            except Exception as e:
                print(f"Error adding PLN to MeTTa: {e}")
                continue
                
            # Test each Q&A pair
            qa_results = []
            for qa in qa_conversions:
                try:
                    # Add question statements
                    for stmt in qa["question_conv"].statements:
                        metta.add_to_context(stmt)
                        
                    # Try to prove each answer statement using backward chaining
                    matches = []
                    for ans_stmt in qa["answer_conv"].statements:
                        _, proven = metta.bc(ans_stmt)
                        matches.append(proven)
                        
                    matched = any(matches)
                except Exception as e:
                    print(f"Error during Q&A validation: {e}")
                    matched = False
                    
                qa_results.append({
                    "qa": qa["original"],
                    "matched": matched
                })
                
            results.append({
                "sentence": conv["sentence"],
                "conversion": conv,
                "qa_results": qa_results
            })
            
        return results
        
    def _score_conversions(self, results: List[Dict]) -> Tuple[Dict, float]:
        """Score PLN conversions based on consistency and Q&A success"""
        best_score = 0
        best_conversion = None
        
        for result in results:
            # Calculate percentage of successful Q&A matches
            matches = sum(1 for qa in result["qa_results"] if qa["matched"])
            score = matches / len(result["qa_results"]) if result["qa_results"] else 0
            
            if score > best_score:
                best_score = score
                best_conversion = result["conversion"]
                
        return best_conversion, best_score

def create_training_data():
    """Create training examples for optimization"""
    examples = [
        dspy.Example(
            sentence="All cats are mammals",
            similar_sentences=[
                "Every cat is a mammal",
                "If something is a cat, it must be a mammal",
                "Cats belong to the mammal family"
            ],
            qa_pairs=[
                {"question": "Are cats mammals?", "answer": "Yes"},
                {"question": "What type of animal is a cat?", "answer": "Mammal"}
            ]
        ),
        # Add more examples...
    ]
    return [ex.with_inputs("sentence") for ex in examples]

def optimize_program(program, trainset, mode="light", out="optimized_sentence_analyzer"):
    """Optimize the program using MIPRO"""
    teleprompter = dspy.teleprompt.MIPROv2(
        metric=lambda _, pred: pred.score,  # Use Q&A success rate as metric
        auto=mode,
        verbose=True
    )
    
    optimized = teleprompter.compile(
        program,
        trainset=trainset,
    )
    
    optimized.save(f"{out}.json")
    return optimized

def main():
    # Initialize program
    program = SentenceAnalyzer()
        
    # Configure LM
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022',temperature=0.5)
    dspy.configure(lm=lm)
        
    # Test
    print("\nRunning test with sentence: 'The sky is blue'")
    result = program("The sky is blue")
    print("\nFull result:")
    print(result)
    print("\nResult type:", type(result))
        
    print("\nTypedefs:", result.get("typedefs"))
    print("Statements:", result.get("statements"))
    print("Context:", result.get("context"))
    print("Validation Score:", result.get("validation_score"))
    print("\nValidation Results:")
    for r in result.get("validation_results", []):
        print(f"- Sentence: {r.get('sentence')}")
        print(f"  QA Results: {r.get('qa_results')}")

if __name__ == "__main__":
    main()
