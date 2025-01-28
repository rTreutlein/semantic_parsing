import dspy
from typing import List, Tuple
from dataclasses import dataclass

class ProofAnalyzerSignature(dspy.Signature):
    """Analyzes a failed proof attempt and suggests the next step towards proving the conclusion.

       If one of the statements seems incorrect, remove it from the knowledge base and add a fixed version.
       If there is some kind of rule/statement missing, add it to the knowledge base.

       The finally suggest the next statement we should try to prove. (Posibily the final conclusion otherwise an intermediate step)
       
       If the proof appears impossible don't return an intermediate conclusion to proof.
       Make sure to maintaing the same format as the input.
    """
    premises: str = dspy.InputField(desc="List of (English, PLN) premise pairs",type=str)
    conclusion: str = dspy.InputField(desc="(English, PLN) conclusion pair",type=str)
    kb_statements: List[str] = dspy.InputField(desc="Additional PLN statements in the knowledge base",type=List[str])
    
    statements_to_remove: List[str] = dspy.OutputField(desc="PLN statements that should be removed from KB",type=List[str])
    statements_to_add: List[str] = dspy.OutputField(desc="New PLN statements that should be added to KB",type=List[str])
    intermediate_conclusion: str = dspy.OutputField(desc="The next intermediate conclusion to prove",type=str)

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
        #with dspy.context(lm=dspy.LM('deepseek/deepseek-reasoner')):
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
