import dspy
from typing import List, Tuple
from dataclasses import dataclass

class ProofAnalyzerSignature(dspy.Signature):
    """We have the following premises along with the Conclusion that we would like to proof
       Doing so automatically has failed.
       Your job is help us proof the conclusion.
       Now the likely issue is that the translations from English to PLN are not consistent with each other.
       Such that while individually correct it's not possible to derive the conclusion from the premises.
       If that is the case you can try to fix the pln representation by replacing the the statements with new ones.
       Another possibility is that we are missing some kind of rule/statement if so you can also fix this
       by leaving the input statements empty and adding the missing statements to the output statements.
       If it looks like you have everything to prove the conclusion provide the first proof step (the inputs of this step and the expected output).
       If non of this is possible or the conclusion just doesn't follow from the premises you can say that the proof is impossible.
    """
    premises: str = dspy.InputField(desc="List of (English, PLN) premise pairs",type=str)
    conclusion: str = dspy.InputField(desc="(English, PLN) conclusion pair",type=str)
    kb_statements: List[str] = dspy.InputField(desc="Additional PLN statements in the knowledge base",type=List[str])
    
    action: str = dspy.OutputField(desc="Either 'fix' or 'combine' or 'impossible'",type=str)
    input_statements: List[str] = dspy.OutputField(desc="PLN statements to be replaced/combined",type=List[str])
    output_statements: List[str] = dspy.OutputField(desc="Replacement PLN statements or expected conclusion",type=List[str])

class ProofAnalyzer(dspy.Module):
    """DSPy module for analyzing failed proofs and suggesting fixes"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(ProofAnalyzerSignature)

    def forward(self, premises: List[Tuple[str, str]], 
                conclusion: Tuple[str, str],
                kb_statements: List[str]) -> dspy.Prediction:
        """Analyze proof failure and suggest fixes
        
        Args:
            premises: List of (English, PLN) premise pairs
            conclusion: (English, PLN) conclusion pair
            kb_statements: Additional PLN statements in knowledge base
            
        Returns:
            ProofAnalysisResult with suggested fix
        """
        with dspy.context(lm=dspy.LM('deepseek/deepseek-reasoner')):
            return self.analyzer(
                premises=premises,
                conclusion=conclusion,
                kb_statements=kb_statements
            )
        
def main():
    """Simple test of ProofAnalyzer functionality"""
    
    # Configure DSPy
    lm = dspy.LM('deepseek/deepseek-chat')
    dspy.configure(lm=lm)
    
    # Create analyzer
    analyzer = ProofAnalyzer()
    
    # Test data
    test_data = {
        "premises": "\n".join(["English:\nAll birds can fly\nPLN:\n(: birdCanFly (-> (: $birdPrf (Bird $x)) (CanFly $x)))\n",
                     "English:\nEagles are birds\nPLN:\n(: eagleIsBird (-> (: $eaglePrf (Eagle $x)) (Bird $x)))\n"]),
        "conclusion": "English:\nEagles can fly\nPLN:\n(: eagleCanFly (-> (: $eaglePrf (Eagle $x)) (CanFly $x)))\n",
        "kb_statements": ["(: deduction (-> (: $ab (-> (: $prfa $a) $b)) (-> (: $bc (-> (: $prfb $b) $c)) (-> (: $prfa $a) $c))))"],
    }
    
    # Run analysis
    print("Running Proof Analyzer test...")
    result = analyzer(**test_data)
    print("\nProof Analysis Result:")
    print(result)
    print("History:")
    dspy.inspect_history(n=1)

if __name__ == "__main__":
    main()
