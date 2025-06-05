from typing import List, Tuple
import dspy
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.dspy.type_similarity import TypeSimilarityHandler

class SimpleProofHandler:
    def __init__(self, metta_handler,
                 query: str,
                 premises: List[str]):
        self.metta_handler = metta_handler
        self.query = query
        self.premises = premises

    def try_to_proof(self) -> bool:
        """Attempt to prove conclusion using current KB"""
        print("Trying to proof:")
        for stmt in self.premises:
            print(stmt)
            self.metta_handler.add_atom(stmt)
        
        print("Running backward chaining...")
        print(self.query)
        proof_steps, proven = self.metta_handler.query(self.query)
        print("----------------------------------------------")
        print("Backward Results:")
        print(proven)
        print(proof_steps)

        if not proven:
            print("Failed to prove query")
            #print(self.metta_handler.run("!(show-cs &kb)"))
            #print(self.metta_handler.run("!(compileQuery " + self.query + ")"))
        return proven

class SimplePuzzleProcessor:
    def __init__(self, output_base: str, verify: bool = False):
        self.output_base = output_base
        self.puzzle_counter = 0
        self.n = 5
        
        # Initialize components
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=SimpleNL2PLN(n=self.n),
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_simple_nl2pln.json"
            )
        else:
            self.nl2pln = SimpleNL2PLN(n=self.n)

    def process_puzzle(self, premises: List[str], query: str):
        """Process a complete puzzle with premises and conclusion."""
        print(f"Processing puzzle with {len(premises)} premises")
        
        self.puzzle_counter += 1    
        
        try:
            combined_text = "\n".join(premises) + f"\n{query}"

            # Process combined text
            pln_data = self.nl2pln(combined_text)

            cnt = 0
            res = 0
            for i in range(self.n):
                self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}_{cnt}.metta")
                self.metta_handler.load_kb_from_file()
                cnt += 1
                proof_handler = SimpleProofHandler(
                    self.metta_handler,
                    pln_data[i].questions[0],
                    pln_data[i].statements
                )
                if proof_handler.try_to_proof():
                    res += 1
            print(f"Proved {res}/{cnt} statements")
            return res/cnt
        except Exception as e:
            print(f"Error processing puzzle: {e}")
            raise
