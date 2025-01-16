import dspy
from typing import List, Dict, Tuple, Optional
from hyperon import MeTTa
from NL2PLN.nl2pln import NL2PLN
from .ragclass import RAG
from NL2PLN.metta.metta_handler import MeTTaHandler

class SimilarSentencesSignature(dspy.Signature):
    """Generate semantically idential sentences to the input. That use a differnt structure or wording"""
    original_sentence: str = dspy.InputField()
    similar_sentences: List[str] = dspy.OutputField()

class QuestionAnswerSignature(dspy.Signature):
    """Generate question-answer pairs that can be answered using the input sentence."""
    sentence: str = dspy.InputField()
    qa_pairs: List[Dict[str, str]] = dspy.OutputField()

class ProvenToEnglishSignature(dspy.Signature):
    """Convert a proven PLN statement back to English"""
    proven_statement: str = dspy.InputField()
    english: str = dspy.OutputField()

class ValidateAnswerSignature(dspy.Signature):
    """Check if the proven statement answers the original question"""
    question: str = dspy.InputField()
    expected_answer: str = dspy.InputField()
    proven_english: str = dspy.InputField()
    is_valid: bool = dspy.OutputField()

class SentenceAnalyzer(dspy.Module):
    """Enhanced NL2PLN module that validates conversions through Q&A consistency"""
    
    def __init__(self, rag: Optional[RAG] = None):
        super().__init__()
        self.generate_similar = dspy.ChainOfThought(SimilarSentencesSignature)
        self.generate_qa = dspy.ChainOfThought(QuestionAnswerSignature)
        self.nl2pln = NL2PLN(rag if rag else RAG())
        self.to_english = dspy.ChainOfThought(ProvenToEnglishSignature)
        self.validate_answer = dspy.ChainOfThought(ValidateAnswerSignature)
        
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
        all_sentences = all_sentences[:5]

        print(f"All sentences: {all_sentences}")
        
        # Convert each sentence using NL2PLN with multiple completions
        pln_conversions = []
        for sent in all_sentences:
            print(f"\nProcessing sentence: {sent}")
            pln_data = self.nl2pln.forward(sent, previous_sentences, n=3)
            if hasattr(pln_data, 'completions'):
                print(f"Number of completions: {len(pln_data.completions)}")
                for completion in pln_data.completions:
                    print(f"Completion: {completion.statements}")
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
            print(f"QA pairs: {qa.qa_pairs}")
            qa_pairs.extend(qa.qa_pairs[:3])
            
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
                    metta.add_atom_and_run_fc(stmt)
            except Exception as e:
                print(f"Error adding PLN to MeTTa: {e}")
                continue
                
            # Test each Q&A pair
            qa_results = []
            for qa in qa_conversions:
                matched = False
                try:
                    # Add question statements and get proofs
                    print(f"Question conversion: {qa['question_conv']}")
                    all_proven = []
                    for stmt in qa["question_conv"].questions:
                        res = metta.bc(stmt)
                        if res[0]:  # If we got any proofs
                            proven_statements = [str(x) for x in res[0]]
                            print(f"Proven statements: {proven_statements}")
                    
                            # Convert proven statements back to English
                            proven_english = []
                            for stmt in proven_statements:
                                eng = self.to_english(proven_statement=stmt)
                                proven_english.append(eng.english)
                            
                            # Validate using LLM
                            with dspy.context(lm=dspy.LM('openrouter/meta-llama/llama-3.2-3b-instruct')):
                                print("Validating answer...")
                                print(f"Question: {qa['original']['question']}")
                                print(f"Expected answer: {qa['original']['answer']}")
                                validation = self.validate_answer(
                                    question=qa["original"]["question"],
                                    expected_answer=qa["original"]["answer"],
                                    proven_english="; ".join(proven_english)
                                )
                            matched = validation.is_valid
                        
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
        
    # Load training data
    with open("NL2PLN/data/johnnoperformative.txt", "r") as f:
        training_data = f.read().strip().split("\n")

    print(f"Training data: {training_data}")
    
    # Test with first example
    print("\nRunning test with training data")
    result = program(training_data[0])
        
    print("\nValidation Results:")
    for r in result.get("validation_results", []):
        print(f"\n- Sentence: {r.get('sentence')}")
        qa_results = r.get('qa_results', [])
        matches = sum(1 for qa in qa_results if qa["matched"])
        score = matches / len(qa_results) if qa_results else 0
        print(f"  Score: {score:.2f} ({matches}/{len(qa_results)} Q&A pairs matched)")
        print("  QA Results:")
        for qa in qa_results:
            print(f"    Q: {qa['qa']['question']}")
            print(f"    A: {qa['qa']['answer']}")
            print(f"    Matched: {qa['matched']}")

if __name__ == "__main__":
    main()
