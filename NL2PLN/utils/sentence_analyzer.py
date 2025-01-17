import dspy
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from hyperon import MeTTa
from NL2PLN.nl2pln import NL2PLN
from .ragclass import RAG
from NL2PLN.metta.metta_handler import MeTTaHandler
from .prompts import NL2PLN_Signature

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
        self.nl2pln = NL2PLN(rag)
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

        # Convert each sentence using NL2PLN with multiple completions
        pln_conversions = []
        for sent in all_sentences:
            pln_data = self.nl2pln.forward(sent, previous_sentences, n=5)
            if hasattr(pln_data, 'completions'):
                for completion in pln_data.completions:
                    pln_conversions.append({
                        "sentence": sent,
                        "typedefs": completion.typedefs,
                        "statements": completion.statements,
                        "context": completion.context
                    })
            else:
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
        result = dspy.Prediction(
            typedefs=best_conversion["typedefs"],
            statements=best_conversion["statements"],
            context=best_conversion["context"],
            validation_score=score,
            validation_results=results
        )
        return result
        
    def _validate_single_conversion(self, conv: Dict, qa_conversions: List[Dict]) -> Dict:
        """Process a single PLN conversion with its Q&A pairs"""
        # Create a temporary MeTTa handler for validation
        metta = MeTTaHandler("temp_kb.metta", read_only=True)
        
        # Add type definitions and statements
        for typedef in conv["typedefs"]:
            try:
                metta.add_to_context(typedef)
            except Exception as e:
                print(f"Error adding typedef: {typedef}")
                print(f"Error: {str(e)}")
                return None

        for stmt in conv["statements"]:
            try:
                metta.add_atom_and_run_fc(stmt)
                print(f"Added statement: {stmt}")
            except Exception as e:
                print(f"Error adding statement: {stmt}")
                print(f"Error: {str(e)}")
                return None
            
        # Test each Q&A pair
        qa_results = []
        for qa in qa_conversions:
            print(qa)
            matched = False
            try:
                all_proven = []
                for stmt in qa["question_conv"].questions:
                    print(f"question {stmt}")
                    res = metta.bc(stmt)
                    print(f"result {res}")
                    if res[0]:  # If we got any proofs
                        proven_statements = [str(x) for x in res[0]]
                        
                        # Convert proven statements back to English
                        proven_english = []
                        for stmt in proven_statements:
                            eng = self.to_english(proven_statement=stmt)
                            proven_english.append(eng.english)
                        
                        # Validate using LLM
                        with dspy.context(lm=dspy.LM('openrouter/meta-llama/llama-3.2-3b-instruct')):
                            validation = self.validate_answer(
                                question=qa["original"]["question"],
                                expected_answer=qa["original"]["answer"],
                                proven_english="; ".join(proven_english)
                            )
                        matched = validation.is_valid
                    
            except Exception:
                matched = False
                
            qa_results.append({
                "qa": qa["original"],
                "matched": matched
            })
            
        return {
            "sentence": conv["sentence"],
            "conversion": conv,
            "qa_results": qa_results
        }

    def _validate_inference(self, pln_conversions: List[Dict], 
                          qa_conversions: List[Dict]) -> List[Dict]:
        """Run inference validation for each PLN conversion in parallel"""
        results = []
        
        print(pln_conversions)
        print(qa_conversions)
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all conversions to the thread pool
            future_to_conv = {
                executor.submit(self._validate_single_conversion, conv, qa_conversions): conv 
                for conv in pln_conversions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_conv):
                result = future.result()
                if result is not None:
                    results.append(result)
        
        return results
        
    def _score_conversions(self, results: List[Dict]) -> Tuple[Dict, float]:
        """Score PLN conversions based on consistency and Q&A success, with length as tie breaker"""
        best_score = 0
        best_length = float('inf')  # Initialize with infinity for length comparison
        best_conversion = None
        
        for result in results:
            # Calculate percentage of successful Q&A matches
            matches = sum(1 for qa in result["qa_results"] if qa["matched"])
            score = matches / len(result["qa_results"]) if result["qa_results"] else 0
            
            # Get length of PLN conversion (total number of statements)
            conv_length = len(result["conversion"]["statements"])
            
            # Update best if:
            # 1. Score is better OR
            # 2. Score is equal but conversion is shorter
            if score > best_score or (score == best_score and conv_length < best_length):
                best_score = score
                best_length = conv_length
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
        metric=lambda _, pred: pred.validation_score,  # Use Q&A success rate as metric
        auto=mode,
        verbose=True,
        num_threads=1,
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
    #lm = dspy.LM('deepseek/deepseek-chat',temperature=1)
    dspy.configure(lm=lm)
        
    # Load training data
    with open("NL2PLN/data/johnnoperformative.txt", "r") as f:
        training_data = f.read().strip().split("\n")
        training_data = [dspy.Example(sentence=s).with_inputs('sentence') for s in training_data]

    #program = optimize_program(program, training_data)

    # Test with first example
    result = program("Every boy on vashon has a dog which every girl on vashon likes to call by a special pet name.")

    print("\nValidation Results:")                                                                                                                                                   
    for r in result.validation_results:
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
