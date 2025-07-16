from typing import List, Tuple
import dspy
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.mettalog_handler import MettalogHandler, TimeoutError
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.dspy.type_similarity import TypeSimilarityHandler

class SimpleProofHandler:
    def __init__(self, metta_handler, log: bool = True):
        self.metta_handler = metta_handler
        self.log = log

    def try_to_proof(self, pln_data, idx, timeout: float = 300.0) -> bool:
        """Attempt to prove conclusion using current KB"""
        query = pln_data.questions[0]
        premises = pln_data.statements

        if self.log:
            logger.info("Trying to proof idx: %s\n%s", idx, pln_data)
        for stmt in premises:
            self.metta_handler.add_atom(stmt)
        if self.log:
            logger.info("Running backward chaining... Idx: %s\n%s", idx, query)
        try:
            proof_steps, proven = self.metta_handler.query(query, log=self.log, timeout=timeout)
        except TimeoutError:
            logger.warning("Query timed out for idx: %s", idx)
            return False
            
        if self.log:
            logger.info("----------------------------------------------")
            logger.info("Backward Results Idx: %s\n%s\n%s", idx, proven, proof_steps)

        if not proven and self.log:
            logger.warning("Failed to prove query Idx: %s", idx)
        return proven

class SimplePuzzleProcessor:
    def __init__(self, output_base: str, nl2pln, verify: bool = False):
        self.output_base = output_base
        self.puzzle_counter = 0
        self.n = nl2pln.n
        
        # Initialize components
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
        metta_handler = MettalogHandler()
        proof_handler = SimpleProofHandler(metta_handler)

        try:
            return proof_handler.try_to_proof(pln_data[i], i, timeout=300.0)
        except TimeoutError:
            logger.warning("Proof %s timed out", i)
            return False

    def process_puzzle(self, puzzle: dspy.Prediction):
        """Process a complete puzzle with premises and conclusion."""
        premises = puzzle.sentences
        query = puzzle.question
        logger.info("Processing puzzle with %s premises", len(premises))
        
        self.puzzle_counter += 1    
        
        try:
            combined_text = "\n".join(premises) + f"\n{query}"

            # Process combined text
            pln_data = self.nl2pln(combined_text)

            # Run proofs in parallel
            res = 0
            reslist = []
            with ThreadPoolExecutor(max_workers=min(self.n, 8)) as executor:
                futures = [executor.submit(self._run_single_proof, i, pln_data, self.puzzle_counter) for i in range(self.n)]
                reslist = [f.result() for f in futures]

            for elem in reslist:
                if elem:
                    res += 1
            
            logger.info("Proved %s/%s statements", res, self.n)
            return res/self.n
        except Exception as e:
            logger.error("Error processing puzzle: %s", e)
            raise
