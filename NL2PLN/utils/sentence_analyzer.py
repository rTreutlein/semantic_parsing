import dspy
from typing import List, Dict, Tuple
from hyperon import MeTTa

class SimilarSentencesSignature(dspy.Signature):
    """Generate semantically similar sentences to the input.
    Make sure the generated sentences:
    - Preserve the exact same meaning as the original
    - Use different wording/structure where possible
    - Are grammatically correct
    - Are natural sounding
    """
    
    original_sentence: str = dspy.InputField(desc="Original sentence to generate variations for")
    similar_sentences: List[str] = dspy.OutputField(desc="List of sentences with same meaning")

class QuestionAnswerSignature(dspy.Signature):
    """Generate question-answer pairs that can be answered using the input sentence.
    Make sure:
    - Questions are directly answerable from the sentence content
    - Answers are concise and specific
    - Both questions and answers use natural language
    """
    
    sentence: str = dspy.InputField(desc="Sentence to generate QA pairs for")
    qa_pairs: List[Dict[str, str]] = dspy.OutputField(desc="List of question-answer pairs")

class PLNConversionSignature(dspy.Signature):
    """Convert natural language to PLN format.
    Ensure:
    - All logical relationships are preserved
    - Variables and predicates follow PLN syntax
    - The conversion is complete and valid
    """
    
    sentence: str = dspy.InputField(desc="Natural language sentence to convert")
    pln: str = dspy.OutputField(desc="PLN conversion of the sentence")

class SentenceAnalyzer(dspy.Module):
    """Pipeline for analyzing and converting sentences with validation through Q&A"""
    
    def __init__(self):
        super().__init__()
        self.generate_similar = dspy.ChainOfThought(SimilarSentencesSignature)
        self.generate_qa = dspy.ChainOfThought(QuestionAnswerSignature)
        self.convert_pln = dspy.ChainOfThought(PLNConversionSignature)
        self.metta = MeTTa()
        
    def forward(self, sentence: str) -> Dict:
        """
        Run the full analysis pipeline:
        1. Generate similar sentences
        2. Convert all sentences to PLN (multiple attempts per sentence)
        3. Generate Q&A pairs for each sentence
        4. Convert Q&A to PLN
        5. Validate through inference
        6. Score and rank conversions
        
        Args:
            sentence: Original sentence to analyze
            
        Returns:
            Dict containing:
            - best_pln: Best PLN conversion
            - score: Consistency score
            - qa_results: Question answering results
        """
        # Generate similar sentences
        similar = self.generate_similar(original_sentence=sentence)
        all_sentences = [sentence] + similar.similar_sentences
        
        # Convert each sentence to PLN multiple times
        pln_conversions = []
        for sent in all_sentences:
            for _ in range(3):  # Try 3 conversions per sentence
                pln = self.convert_pln(sentence=sent)
                pln_conversions.append((sent, pln.pln))
                
        # Generate Q&A pairs for each sentence
        qa_pairs = []
        for sent in all_sentences:
            qa = self.generate_qa(sentence=sent)
            qa_pairs.extend(qa.qa_pairs)
            
        # Convert Q&A to PLN
        qa_pln = []
        for qa in qa_pairs:
            q_pln = self.convert_pln(sentence=qa["question"])
            a_pln = self.convert_pln(sentence=qa["answer"])
            qa_pln.append({
                "original": qa,
                "question_pln": q_pln.pln,
                "answer_pln": a_pln.pln
            })
            
        # Validate through inference
        results = self._validate_inference(pln_conversions, qa_pln)
        
        # Score and select best conversion
        best_pln, score = self._score_conversions(results)
        
        return {
            "best_pln": best_pln,
            "score": score,
            "qa_results": results
        }
        
    def _validate_inference(self, pln_conversions: List[Tuple[str, str]], 
                          qa_pln: List[Dict]) -> List[Dict]:
        """Run inference validation for each PLN conversion"""
        results = []
        
        for orig_sent, pln in pln_conversions:
            # Reset MeTTa space
            self.metta.run("!(bind! &kb (new-space))")
            
            # Add the sentence conversion
            try:
                self.metta.run(f"!(add-atom &kb {pln})")
            except:
                continue
                
            # Test each Q&A pair
            qa_results = []
            for qa in qa_pln:
                try:
                    # Try to prove the answer from the question
                    res = self.metta.run(f"""
                        !(let* (
                            ($question {qa['question_pln']})
                            ($answer {qa['answer_pln']})
                        )
                        (if (= $question $answer) "true" "false"))
                    """)
                    matched = res[0] == "true"
                except:
                    matched = False
                    
                qa_results.append({
                    "qa": qa["original"],
                    "matched": matched
                })
                
            results.append({
                "sentence": orig_sent,
                "pln": pln,
                "qa_results": qa_results
            })
            
        return results
        
    def _score_conversions(self, results: List[Dict]) -> Tuple[str, float]:
        """Score PLN conversions based on consistency and Q&A success"""
        best_score = 0
        best_pln = None
        
        for result in results:
            # Calculate percentage of successful Q&A matches
            matches = sum(1 for qa in result["qa_results"] if qa["matched"])
            score = matches / len(result["qa_results"]) if result["qa_results"] else 0
            
            if score > best_score:
                best_score = score
                best_pln = result["pln"]
                
        return best_pln, best_score

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

def optimize_program(program, trainset, mode="medium", out="optimized_sentence_analyzer"):
    """Optimize the program using MIPRO"""
    teleprompter = dspy.teleprompt.MIPROv2(
        metric=lambda ex, pred: pred.score,  # Use Q&A success rate as metric
        auto=mode,
        verbose=True
    )
    
    optimized = teleprompter.compile(
        program.deepcopy(),
        trainset=trainset,
        max_bootstrapped_demos=5,
        max_labeled_demos=5
    )
    
    optimized.save(f"{out}.json")
    return optimized

def main():
    # Initialize program
    program = SentenceAnalyzer()
    
    # Configure LM
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
    dspy.configure(lm=lm)
    
    # Create training data
    trainset = create_training_data()
    
    # Optimize
    program = optimize_program(program, trainset)
    
    # Test
    result = program("The sky is blue")
    print(f"Best PLN: {result.best_pln}")
    print(f"Score: {result.score}")
    print("Q&A Results:")
    for qa in result.qa_results:
        print(f"- {qa}")

if __name__ == "__main__":
    main()
