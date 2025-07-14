from typing import List, Tuple
import dspy
from concurrent.futures import ThreadPoolExecutor, as_completed
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
#from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.metta.mettalog_handler import MettalogHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.dspy.type_similarity import TypeSimilarityHandler

class SimpleProofHandler:
    def __init__(self, metta_handler, log: bool = True):
        self.metta_handler = metta_handler
        self.log = log

    def try_to_proof(self,pln_data,idx) -> bool:
        """Attempt to prove conclusion using current KB"""
        query = pln_data.questions[0]
        premises = pln_data.statements

        if self.log:
            print("Trying to proof idx: " + str(idx) + "\n" + pln_data)
        for stmt in premises:
            #if self.log:
                #print(stmt)
            self.metta_handler.add_atom(stmt)
        if self.log:
            print("Running backward chaining... Idx: " + str(idx) + "\n" + query)
        proof_steps, proven = self.metta_handler.query(query)
        if self.log:
            print("----------------------------------------------")
            print("Backward Results Idx: " + str(idx) + "\n" + proven + "\n" + proof_steps)

        if not proven and self.log:
            print("Failed to prove query Idx: " + str(idx))
        return proven

class SimplePuzzleProcessor:
    def __init__(self, output_base: str, nl2pln, verify: bool = False):
        self.output_base = output_base
        self.puzzle_counter = 0
        self.n = nl2pln.n
        
        # Initialize components
        #self.metta_handler = MettalogHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.metta_handler = MettalogHandler()
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=nl2pln,
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_simple_nl2pln.json"
            )
        else:
            self.nl2pln = nl2pln

    def _run_single_proof(self, i: int, pln_data, puzzle_counter: int) -> bool:
        """Run a single proof attempt - helper method for parallel execution."""
        #metta_handler = MettalogHandler(f"{self.output_base}_{puzzle_counter}_{i}.metta")
        metta_handler = MettalogHandler()
        
        proof_handler = SimpleProofHandler(metta_handler)

        return proof_handler.try_to_proof(pln_data[i],i)

    def process_puzzle(self, puzzle: dspy.Prediction):
        """Process a complete puzzle with premises and conclusion."""
        premises = puzzle.sentences
        query = puzzle.question
        print(f"Processing puzzle with {len(premises)} premises")
        
        self.puzzle_counter += 1    
        
        try:
            combined_text = "\n".join(premises) + f"\n{query}"

            # Process combined text
            pln_data = self.nl2pln(combined_text)

            # Run proofs in parallel
            res = 0
            with ThreadPoolExecutor(max_workers=min(self.n, 8)) as executor:
                # Submit all proof tasks
                future_to_index = {
                    executor.submit(self._run_single_proof, i, pln_data, self.puzzle_counter): i 
                    for i in range(self.n)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_index):
                    i = future_to_index[future]
                    try:
                        if future.result():
                            res += 1
                    except Exception as e:
                        print(f"Error in proof {i}: {e}")
            
            print(f"Proved {res}/{self.n} statements")
            return res/self.n
        except Exception as e:
            print(f"Error processing puzzle: {e}")
            raise
