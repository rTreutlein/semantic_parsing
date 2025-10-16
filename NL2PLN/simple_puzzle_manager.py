from typing import List, Tuple
import dspy
import time
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor

#from NL2PLN.metta.mettalog_handler import MettalogHandler, TimeoutError

from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.dspy.type_similarity import TypeSimilarityHandler

import sys
sys.path.append("/nexus/Dev/OpenCog/MM2Chainer/")

from mork_handler import MorkHandler

class SimpleProofHandler:
    def __init__(self, metta_handler : MorkHandler, log: bool = True):
        self.metta_handler = metta_handler
        self.log = log

    def try_to_proof(self, pln_premises, pln_query, idx, timeout: float = 300.0) -> Tuple[bool, List[str]]:
        """Attempt to prove conclusion using current KB"""
        premises = pln_premises.statements
        query = pln_query.questions[0]
        logger.info("Trying to proof query: %s", pln_query)

        #if self.log:
            #logger.info("Trying to proof idx: %s\n%s", idx, pln_data)
        for stmt in premises:
            logger.info("Adding atom: %s", stmt)
            self.metta_handler.add_atom(stmt)
        if self.log:
            logger.info("Running backward chaining... Idx: %s\n%s", idx, query)

        proofs = self.metta_handler.query(query)

        proven = len(proofs) > 0
            
        if self.log:
            logger.info("----------------------------------------------")
            logger.info("Backward Results Idx: %s\n%s\n%s", idx, proven, proofs)

        if not proven and self.log:
            logger.warning("Failed to prove query Idx: %s", idx)
        return proven, proofs

class SimplePuzzleProcessor:
    def __init__(self, output_base: str, nl2pln, verify: bool = False, n=1):
        self.output_base = output_base
        self.puzzle_counter = 0
        self.n = n
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=nl2pln,
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_simple_nl2pln.json"
            )
        else:
            self.nl2pln = nl2pln

    def _run_single_proof(self, i: int, pln_premises : dspy.Prediction , pln_queries : dspy.Prediction , query : str, expected_answer : str) -> bool:
        """Run a single proof attempt - helper method for parallel execution."""
        metta_handler = MorkHandler()
        proof_handler = SimpleProofHandler(metta_handler)
        logger.info("Initialized proof handler")

        proven , proof_steps = proof_handler.try_to_proof(pln_premises, pln_queries[i], i, timeout=120.0)
        if proven:
            logger.info("Proof %s succeeded", i)
            compare = dspy.ChainOfThought("question, expected_answer, found_proof -> proof_matches_expected_answer : bool")
            comparison = compare(question=query, expected_answer=expected_answer, found_proof=proof_steps)
            logger.info("Proof matches expected answer with reasonign: %s", comparison.reasoning)
            return comparison.proof_matches_expected_answer
        else:
            logger.info("Proof %s failed", i)
            return False

    def process_puzzle(self, puzzle: dspy.Prediction):
        """Process a complete puzzle with premises and conclusion."""
        premises = puzzle.sentences
        query = puzzle.question
        expected_answer = puzzle.expected_answer
        logger.info("Processing puzzle with %s premises", len(premises))
        logger.info("Expected answer: %s", expected_answer)
        
        self.puzzle_counter += 1
        
        try:
            start = time.time()
            pln_premises = self.nl2pln(premises)
            context = f"Converted Sentences:\n{"\n".join(premises)}\nTo: TypeDefs:\n {pln_premises.typedefs} Statements:\n{pln_premises.statements}"
            stop = time.time()
            logger.info(f"Time to convert sentences: {stop - start}")
            
            # Convert query to pln_query multiple times in parallel
            #with ThreadPoolExecutor(max_workers=min(self.n, 8)) as executor:
            #    # Run query conversion in parallel
            #    conversion_futures = [executor.submit(self.nl2pln, query, previous_sentences=context) for i in range(self.n)]
            #    pln_queries = [f.result() for f in conversion_futures]

            start = time.time()
            pln_query = self.nl2pln(query, previous_sentences=context)
            stop = time.time()
            logger.info(f"Time to convert query: {stop - start}")

            res = 0
            start = time.time()
            reslist = [self._run_single_proof(0, pln_premises, [pln_query], query, expected_answer)]
            stop = time.time()
            logger.info(f"Time to run proof: {stop - start}")

            # Run proofs in parallel, using different query conversions
            #with ThreadPoolExecutor(max_workers=min(self.n, 8)) as executor:
            #    futures = [executor.submit(self._run_single_proof, i, pln_premises, pln_queries, query, expected_answer) for i in range(self.n)]
            #    reslist = [f.result() for f in futures]

            for elem in reslist:
                if elem:
                    res += 1
            
            logger.info("Proved %s/%s statements", res, self.n)
            print(res)
            return res/self.n
        except Exception as e:
            logger.error("Error processing puzzle: %s", e)
            raise
