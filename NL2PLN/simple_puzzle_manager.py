from typing import List, Tuple
import dspy
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.dspy.type_similarity import TypeSimilarityHandler

class SimpleSentenceHandler:
    def __init__(self, metta_handler, type_handler, nl2pln):
        self.metta_handler = metta_handler
        self.type_handler = type_handler
        self.nl2pln = nl2pln
        self.previous_sentences = []
        self.pending_statements = []
        self.linking_statements = []

    def process_type_definitions(self, pln_data) -> bool:
        """Process and validate type definitions."""
        for type_def in pln_data.typedefs:
            conflict = self.metta_handler.add_to_context(type_def)
            if isinstance(conflict, str):
                print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
                input("Press Enter to continue...")
                return False
                
        linking_statements = self.type_handler.stage_new_typedefs(pln_data.typedefs)
        self.linking_statements.extend(linking_statements)
        print(f"Found {len(linking_statements)} linking statements")
        print(linking_statements)

        for linking_stmt in linking_statements:
            conflict = self.metta_handler.add_to_context(linking_stmt)
            if isinstance(conflict, str):
                print(f"WARNING: Type relationship {linking_stmt} conflicts with existing atom: {conflict}")
                input("Press Enter to continue...")
                return False
        
        return True

    def process_sentence(self, line: str) -> bool:
        """Process a single sentence."""
        print(f"Processing line: {line}")
        
        recent_context = self.previous_sentences[-10:] if self.previous_sentences else []
        pln_data = self.nl2pln(line, previous_sentences=recent_context)
        print(pln_data)
        
        if pln_data.statements[0] == "Performative":
            return True
            
        if not self.process_type_definitions(pln_data):
            return False
            
        self.pending_statements.extend(pln_data.statements)
        
        self.previous_sentences.append(f"Converted Sentence:\n{line}\nTo: TypeDefs:\n {pln_data.typedefs} Statements:\n{pln_data.statements} Questions:\n{pln_data.questions}")
        if len(self.previous_sentences) > 10:
            self.previous_sentences.pop(0)
        
        return True

class SimpleProofHandler:
    def __init__(self, metta_handler, proof_analyzer, 
                 conclusion_english: str, conclusion_pln: str,
                 pending_statements: List[str],
                 linking_statements: List[str]):
        self.metta_handler = metta_handler
        self.proof_analyzer = proof_analyzer
        self.conclusion_english = conclusion_english
        self.conclusion_pln = conclusion_pln
        self.pending_statements = pending_statements
        self.linking_statements = linking_statements

    def try_to_proof(self) -> bool:
        """Attempt to prove conclusion using current KB"""
        print("Trying to proof:")
        for stmt in self.pending_statements:
            print(stmt)
            self.metta_handler.add_atom(stmt)
        
        print("Running backward chaining...")
        print(self.conclusion_pln)
        proof_steps, proven = self.metta_handler.query(self.conclusion_pln)
        print("----------------------------------------------")
        print("Backward Results:")
        print(proven)
        print(proof_steps)

        if not proven:
            print("Handling failed conclusion")
            print(self.metta_handler.run("!(show-cs &kb)"))
            print(self.metta_handler.run("!(compileQuery " + self.conclusion_pln + ")"))
            return self._handle_failed_conclusion()
        return proven

    def _handle_failed_conclusion(self) -> bool:
        # Simplified version - just return False for failed proofs
        # Could be extended with proof analysis if needed
        print("Proof failed - no further analysis implemented in simple version")
        return False

class SimplePuzzleProcessor:
    def __init__(self, output_base: str, verify: bool = False):
        self.output_base = output_base
        self.puzzle_counter = 0
        
        # Initialize components
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.type_handler = TypeSimilarityHandler(collection_name=f"{output_base}_types", reset_db=True, verify=verify)
        
        self.proof_analyzer = VerifiedPredictor(
            predictor=ProofAnalyzer(),
            verify_func=human_verify_prediction,
            cache_file="verified_proof_analysis_cache.json",
            verify_kwargs=["premises", "conclusion","kb_statements"],
        )
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=SimpleNL2PLN(),
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_simple_nl2pln.json"
            )
        else:
            self.nl2pln = SimpleNL2PLN()

        self.sentence_handler = SimpleSentenceHandler(self.metta_handler, self.type_handler, self.nl2pln)

    def process_conclusion(self, conclusion: str):
        """Process and verify the conclusion."""
        if not conclusion.strip():
            return
            
        print("\nProcessing conclusion:")
        recent_context = self.sentence_handler.previous_sentences[-10:] if self.sentence_handler.previous_sentences else []
        pln_data = self.nl2pln("Is it true that " + conclusion, previous_sentences=recent_context)
        print(pln_data)
        
        if pln_data == "Performative":
            return

        if len(pln_data.questions) > 1:
            print(f"Error expecting only a single question")
            return

        proof_handler = SimpleProofHandler(
            self.metta_handler,
            self.proof_analyzer,
            conclusion,
            pln_data.questions[0],
            self.sentence_handler.pending_statements,
            self.sentence_handler.linking_statements
        )
        if proof_handler.try_to_proof():
            print("Proved conclusion")
            self.sentence_handler.pending_statements = []
            return True

        return False

    def process_batch(self, premises: List[str], conclusion: str) -> bool:
        """Process a batch of premises and conclusion together."""
        combined_text = "\n".join(premises) + f"\nIs it true that {conclusion}"
        
        # Process combined text
        recent_context = self.sentence_handler.previous_sentences[-10:] if self.sentence_handler.previous_sentences else []
        pln_data = self.nl2pln(combined_text, previous_sentences=recent_context)
        print(pln_data)
        
        if not self.sentence_handler.process_type_definitions(pln_data):
            print("Failed to process type definitions, stopping early")
            self.type_handler.clear_pending_types()
            return False
        
        # Store all statements
        self.sentence_handler.pending_statements.extend(pln_data.statements)

        proof_handler = SimpleProofHandler(
            self.metta_handler,
            self.proof_analyzer,
            conclusion,
            pln_data.questions[0],
            self.sentence_handler.pending_statements,
            self.sentence_handler.linking_statements
        )
        # Try to prove the conclusion
        if not proof_handler.try_to_proof():
            print("Failed to prove conclusion")
            self.type_handler.clear_pending_types()
            return False
        
        print("Proved conclusion!")
        return True

    def process_puzzle(self, premises: List[str], conclusion: str):
        """Process a complete puzzle with premises and conclusion."""
        print(f"Processing puzzle with {len(premises)} premises")
        
        self.puzzle_counter += 1    
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.metta_handler.load_kb_from_file()
        
        # Update handlers with new metta_handler
        self.sentence_handler.metta_handler = self.metta_handler
        
        try:
            if self.process_batch(premises, conclusion):
                self.type_handler.commit_pending_types()
                return True
            else:
                self.type_handler.clear_pending_types()
                return False
            
        except Exception as e:
            print(f"Error processing puzzle: {e}")
            self.type_handler.clear_pending_types()
            raise
