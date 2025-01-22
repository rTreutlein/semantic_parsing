import dspy
from NL2PLN.utils.prompts import PLN2NL_Signature, NL2PLN_Signature
from typing import List, Dict

class RoundtripConsistencyCheck(dspy.Module):
    """Checks consistency by converting PLN to English and back to PLN"""
    
    def __init__(self):
        super().__init__()
        self.pln2nl = dspy.ChainOfThought(PLN2NL_Signature)
        self.nl2pln = dspy.ChainOfThought(NL2PLN_Signature)

    def forward(self, pln_statement: str) -> Dict:
        """
        Performs roundtrip conversion: PLN -> English -> PLN
        
        Args:
            pln_statement: The original PLN statement to check
            
        Returns:
            Dictionary containing:
            - original_pln: The input PLN statement
            - english: The intermediate English translation
            - final_pln: The PLN statement after roundtrip
            - is_consistent: Boolean indicating if original and final PLN match
        """
        # Convert PLN to English
        english_result = self.pln2nl(pln=pln_statement)
        english = english_result.english
        
        # Convert back to PLN
        pln_result = self.nl2pln(sentence=english)
        final_pln = pln_result.pln
        
        # Compare original and final PLN statements
        # Note: May need more sophisticated comparison than exact match
        is_consistent = pln_statement.strip() == final_pln.strip()
        
        return {
            "original_pln": pln_statement,
            "english": english,
            "final_pln": final_pln,
            "is_consistent": is_consistent
        }

