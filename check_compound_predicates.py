import re
from typing import List, Tuple
from utils.llm_client import OpenAIClient
import os

class CompoundPredicateChecker:
    def __init__(self):
        self.llm_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_predicates(self, metta_atom: str) -> List[str]:
        """
        Extract predicates from a MeTTa atom.
        """
        predicate_pattern = r'\(([^()]+)\)'
        return re.findall(predicate_pattern, metta_atom)

    def check_compound_predicates(self, predicates: List[str]) -> List[str]:
        """
        Use LLM to check if predicates are compound.
        """
        prompt = f"""
        Given the following list of predicates, identify which ones are compound (contain multiple concepts):
        {', '.join(predicates)}

        Return only the compound predicates, separated by commas.
        """
        response = self.llm_client.generate(prompt)
        return [pred.strip() for pred in response.split(',') if pred.strip()]

    def generate_equivalence(self, compound_predicate: str) -> str:
        """
        Use LLM to generate the predicate logic equivalence of a compound predicate.
        """
        prompt = f"""
        Generate the predicate logic equivalence for the compound predicate: {compound_predicate}

        Use the following format:
        ∀ $x (CompoundPredicate($x) ↔ (Predicate1($x) ∧ Predicate2($x) ∧ ...))

        Return only the equivalence statement.
        """
        return self.llm_client.generate(prompt)

    def check_and_generate_equivalences(self, metta_atom: str) -> List[Tuple[str, str]]:
        """
        Check for compound predicates in a MeTTa atom and generate their equivalences using LLM.
        """
        predicates = self.extract_predicates(metta_atom)
        compound_predicates = self.check_compound_predicates(predicates)
        equivalences = []

        for predicate in compound_predicates:
            equivalence = self.generate_equivalence(predicate)
            equivalences.append((predicate, equivalence))

        return equivalences

# Example usage
if __name__ == "__main__":
    checker = CompoundPredicateChecker()
    metta_atom = "(= (LargeRedBall $x) (and (Ball $x) (Large $x) (Red $x)))"
    results = checker.check_and_generate_equivalences(metta_atom)
    
    for compound, equivalence in results:
        print(f"Compound Predicate: {compound}")
        print(f"Generated Equivalence: {equivalence}")
        print()
