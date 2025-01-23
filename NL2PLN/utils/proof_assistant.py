import dspy
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass 
class ProofAnalysisResult:
    """Result structure for proof analysis"""
    action: str
    premise_index: Optional[int] = None
    fixed_pln: Optional[str] = None
    statement1: Optional[str] = None
    statement2: Optional[str] = None
    combination_rule: Optional[str] = None

class ProofAnalyzerSignature(dspy.Signature):
    """Signature for proof analysis module"""
    premises_english = dspy.InputField(List[str])
    premises_pln = dspy.InputField(List[str])
    conclusion_english = dspy.InputField(str)
    conclusion_pln = dspy.InputField(str)
    existing_proof_steps = dspy.InputField(List[str])
    
    action = dspy.OutputField(str, desc="Either 'fix_premise' or 'combine_statements'")
    premise_index = dspy.OutputField(Optional[int], desc="Index of premise to fix")
    fixed_pln = dspy.OutputField(Optional[str], desc="Corrected PLN statement")
    statement1 = dspy.OutputField(Optional[str], desc="First statement to combine")
    statement2 = dspy.OutputField(Optional[str], desc="Second statement to combine")
    combination_rule = dspy.OutputField(Optional[str], desc="Rule for combining statements")

class ProofAnalyzer(dspy.Module):
    """DSPy module for analyzing failed proofs and suggesting fixes"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(ProofAnalyzerSignature)

    def forward(self, premises_english: List[str], premises_pln: List[str],
                conclusion_english: str, conclusion_pln: str,
                existing_proof_steps: List[str]) -> ProofAnalysisResult:
        """Analyze proof failure and suggest fixes
        
        Args:
            premises_english: List of premises in English
            premises_pln: List of premises in PLN
            conclusion_english: Conclusion in English
            conclusion_pln: Conclusion in PLN
            existing_proof_steps: Current proof steps
            
        Returns:
            ProofAnalysisResult with suggested fix
        """
        result = self.analyzer(
            premises_english=premises_english,
            premises_pln=premises_pln,
            conclusion_english=conclusion_english,
            conclusion_pln=conclusion_pln,
            existing_proof_steps=existing_proof_steps
        )
        
        return ProofAnalysisResult(
            action=result.action,
            premise_index=result.premise_index,
            fixed_pln=result.fixed_pln,
            statement1=result.statement1,
            statement2=result.statement2,
            combination_rule=result.combination_rule
        )

def main():
    """Simple test of ProofAnalyzer functionality"""
    
    # Configure DSPy
    dspy.settings.configure(lm="anthropic/claude-3-sonnet-20240229")
    
    # Create analyzer
    analyzer = ProofAnalyzer()
    
    # Test data
    test_data = {
        "premises_english": ["All birds can fly", "Penguins are birds"],
        "premises_pln": ["(ForAll $x (Implication (Bird $x) (CanFly $x)))", 
                        "(ForAll $x (Implication (Penguin $x) (Bird $x)))"],
        "conclusion_english": "Penguins can fly",
        "conclusion_pln": "(ForAll $x (Implication (Penguin $x) (CanFly $x)))",
        "existing_proof_steps": []
    }
    
    # Run analysis
    print("Running Proof Analyzer test...")
    result = analyzer(**test_data)
    print("\nProof Analysis Result:")
    print(result)

if __name__ == "__main__":
    main()
