import re
from typing import List, Tuple

def extract_predicates(metta_atom: str) -> List[str]:
    """
    Extract predicates from a MeTTa atom.
    """
    predicate_pattern = r'\(([^()]+)\)'
    return re.findall(predicate_pattern, metta_atom)

def is_compound_predicate(predicate: str) -> bool:
    """
    Check if a predicate is compound (contains multiple words).
    """
    return len(predicate.split()) > 1

def split_compound_predicate(predicate: str) -> List[str]:
    """
    Split a compound predicate into its constituent parts.
    """
    return predicate.split()

def generate_equivalence(compound_predicate: str, constituents: List[str]) -> str:
    """
    Generate the predicate logic equivalence of a compound predicate to its constituents.
    """
    compound_var = f"${compound_predicate.replace(' ', '_')}"
    constituent_vars = [f"${const}" for const in constituents]
    
    left_side = f"{compound_predicate}({compound_var})"
    right_side = " ∧ ".join([f"{const}({var})" for const, var in zip(constituents, constituent_vars)])
    
    return f"∀ {compound_var} ({left_side} ↔ ({right_side}))"

def check_and_generate_equivalences(metta_atom: str) -> List[Tuple[str, str]]:
    """
    Check for compound predicates in a MeTTa atom and generate their equivalences.
    """
    predicates = extract_predicates(metta_atom)
    equivalences = []

    for predicate in predicates:
        if is_compound_predicate(predicate):
            constituents = split_compound_predicate(predicate)
            equivalence = generate_equivalence(predicate, constituents)
            equivalences.append((predicate, equivalence))

    return equivalences

# Example usage
if __name__ == "__main__":
    metta_atom = "(= (LargeRedBall $x) (and (Ball $x) (Large $x) (Red $x)))"
    results = check_and_generate_equivalences(metta_atom)
    
    for compound, equivalence in results:
        print(f"Compound Predicate: {compound}")
        print(f"Equivalence: {equivalence}")
        print()
