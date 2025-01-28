from typing import List, Tuple
import dspy
from NL2PLN.utils.proof_assistant import ProofAnalyzer
from NL2PLN.nl2pln import NL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.type_similarity import TypeSimilarityHandler

class SentenceHandler:
    def __init__(self, metta_handler, type_handler, nl2pln, rag):
        self.metta_handler = metta_handler
        self.type_handler = type_handler
        self.nl2pln = nl2pln
        self.rag = rag
        self.previous_sentences = []
        self.pending_rag_entries = []
        self.pending_statements = []
        self.linkingStatments = []

    def process_type_definitions(self, pln_data) -> bool:
        """Process and validate type definitions."""
        for type_def in pln_data.typedefs:
            conflict = self.metta_handler.add_to_context(type_def)
            if isinstance(conflict, str):
                print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
                input("Press Enter to continue...")
                return False
                
        linking_statements = self.type_handler.stage_new_typedefs(pln_data.typedefs)
        self.linkingStatments.extend(linking_statements)
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
            
        self.pending_rag_entries.append((line, pln_data))
        self.pending_statements.extend(pln_data.statements)
        
        self.previous_sentences.append(f"Converted Sentence:\n{line}\nTo:\n Context:\n{pln_data.context} TypeDefs:\n {pln_data.typedefs} Statements:\n{pln_data.statements} Questions:\n{pln_data.questions}")
        if len(self.previous_sentences) > 10:
            self.previous_sentences.pop(0)
        
        return True

    def process_section(self, section_name: str, sentences: list[str]):
        """Process a section of sentences."""
        print(f"\nProcessing {section_name}:")
        for sentence in sentences:
            if sentence.strip():
                if not self.process_sentence(sentence):
                    return False
        return True

class ProofHandler:
    def __init__(self, metta_handler, proof_analyzer):
        self.metta_handler = metta_handler
        self.proof_analyzer = proof_analyzer

    def try_to_proof(self, conclusion_english: str, conclusion_pln: str, pending_statements: List[str], pending_rag_entries: List[tuple], linking_statements: List[str]) -> bool:
        """Attempt to prove conclusion using current KB"""
        self.current_conclusion = conclusion_pln  # Store the current conclusion
        print("Trying to proof:")
        for stmt in pending_statements:
            print(stmt)
            self.metta_handler.add_atom_and_run_fc(stmt)
        
        proof_steps, proven = self.metta_handler.bc(conclusion_pln)
        
        if not proven:
            print("Handling failed conclusion")
            premises = [
                (sent, data.statements)
                for sent, data in pending_rag_entries
            ]
            self._handle_failed_conclusion(
                conclusion_english, 
                conclusion_pln,
                premises,
                proof_steps,
                linking_statements
            )
        return proven

    def _handle_failed_conclusion(self, conclusion_english: str, conclusion_pln: str,
                               premises: List[Tuple[str, List[str]]], proof_steps: List[str],
                               linking_statements: List[str]):
        premises_formatted = "\n".join([
            f"English:\n{eng}\nPLN:\n{"\n".join(pln)}" 
            for eng, pln in premises
        ])

        rules = self.metta_handler.get_rules()
        kb_statements = rules + linking_statements
        
        print(f"Running proof analysis with premises:\n{premises_formatted}")
        analysis_result = self.proof_analyzer(
            premises=premises_formatted,
            conclusion=f"English:\n{conclusion_english}\nPLN:\n{conclusion_pln}",
            kb_statements=kb_statements
        )

        print(f"Proof analysis suggests: {analysis_result.action}")
        
        if analysis_result.action == "fix":
            if self._handle_fix_action(analysis_result):
                print("Successfully fixed and proved!")
            else:
                print("Fix attempt unsuccessful")
        elif analysis_result.action == "combine":
            self._handle_combine_action(analysis_result)
        else:
            print("Proof appears impossible. Needs human intervention")

    def _handle_fix_action(self, result: dspy.Prediction):
        """Handle premise fixing suggestions by replacing statements with fixed versions"""
        print(f"Suggested fixes: {result.input_statements} => {result.output_statements}")
        
        # Remove old statements
        for stmt in result.input_statements:
            self.metta_handler.run(f'!(remove-atom &kb {stmt})')
        
        # Add fixed statements
        for stmt in result.output_statements:
            self.metta_handler.run(f'!(add-atom &kb {stmt})')
            
        print("Statements replaced. Rerunning backward chaining...")
        
        # Rerun backward chaining with the modified KB
        proof_steps, proven = self.metta_handler.bc(self.current_conclusion)
        
        if proven:
            print("Proof succeeded after fixes!")
            return True
        else:
            print("Proof still failed after fixes. Further analysis may be needed.")
            return False

    def _handle_combine_action(self, result: dspy.Prediction):
        """Handle statement combination suggestions"""
        print(f"Suggested combinations: {result.input_statements} => {result.output_statements}")

class PuzzleProcessor:
    def __init__(self, output_base: str, reset_db: bool = False, verify: bool = False):
        self.output_base = output_base
        self.processed_premises = set()
        self.puzzle_counter = 0
        
        # Initialize components
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.rag = RAG(collection_name=f"{output_base}_pln", reset_db=reset_db)
        self.type_handler = TypeSimilarityHandler(collection_name=f"{output_base}_types", reset_db=reset_db, verify=verify)
        
        self.proof_analyzer = VerifiedPredictor(
            predictor=ProofAnalyzer(),
            verify_func=human_verify_prediction,
            cache_file="verified_proof_analysis_cache.json",
            verify_kwargs=["premises", "conclusion","kb_statements"],
        )
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=NL2PLN(self.rag),
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_nl2pln.json"
            )
        else:
            self.nl2pln = NL2PLN(self.rag)

        self.sentence_handler = SentenceHandler(self.metta_handler, self.type_handler, self.nl2pln, self.rag)
        self.proof_handler = ProofHandler(self.metta_handler, self.proof_analyzer)

    def store_sentence_results(self, sentence: str, pln_data: dspy.Prediction):
        """Store processed sentence results in RAG."""
        self.rag.store_embedding({
            "sentence": sentence,
            "from_context": pln_data.context,
            "type_definitions": pln_data.typedefs,
            "statements": pln_data.statements,
        }, embedding_fields=["sentence", "statements"])

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
            print(f"Error expection only a single question")
            return

        if self.proof_handler.try_to_proof(
            conclusion, 
            pln_data.questions[0],
            self.sentence_handler.pending_statements,
            self.sentence_handler.pending_rag_entries,
            self.sentence_handler.linkingStatments
        ):
            print("Proved conclusion")
            self.sentence_handler.pending_statements = []
            for sentence, pln_data in self.sentence_handler.pending_rag_entries:
                self.store_sentence_results(sentence, pln_data)
            self.sentence_handler.pending_rag_entries = []
            return True

        return False

    def prepare_combined_text(self, premises: List[str], conclusion: str) -> str:
        """Combine premises and conclusion into a single text."""
        premises_text = " ".join(premises)
        return f"{premises_text} Is it true that {conclusion}"

    def process_batch(self, premises: List[str], conclusion: str) -> bool:
        """Process a batch of premises and conclusion together."""
        combined_text = self.prepare_combined_text(premises, conclusion)
        
        # Process combined text
        recent_context = self.sentence_handler.previous_sentences[-10:] if self.sentence_handler.previous_sentences else []
        pln_data = self.nl2pln(combined_text, previous_sentences=recent_context)
        #premises will be the statements
        #conclusion will be the question
        print(pln_data)
        
        if not self.sentence_handler.process_type_definitions(pln_data):
            print("Failed to process type definitions, stopping early")
            self.type_handler.clear_pending_types()
            return False
        
        # Store all statements
        self.sentence_handler.pending_statements.extend(pln_data.statements)
        self.sentence_handler.pending_rag_entries.append((combined_text, pln_data))
        
        # Try to prove the conclusion (last statement)
        if not self.proof_handler.try_to_proof(
            conclusion,
            pln_data.questions[0],
            self.sentence_handler.pending_statements,
            self.sentence_handler.pending_rag_entries,
            self.sentence_handler.linkingStatments
        ):
            print("Failed to prove conclusion, discarding pending entries")
            self.sentence_handler.pending_rag_entries = []
            self.type_handler.clear_pending_types()
            return False
        
        # Store results
        for sentence, pln_data in self.sentence_handler.pending_rag_entries:
            self.store_sentence_results(sentence, pln_data)
        self.sentence_handler.pending_rag_entries = []
        return True

    def process_puzzle(self, puzzle_sections: dict):
        """Process a complete puzzle."""
        print(puzzle_sections)
        
        self.puzzle_counter += 1    
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.metta_handler.load_kb_from_file()
        
        # Update handlers with new metta_handler
        self.sentence_handler.metta_handler = self.metta_handler
        self.proof_handler.metta_handler = self.metta_handler
        
        deductions = puzzle_sections.get('deduction', [])
        
        try:
            for required_premises, conclusion in deductions:
                new_premises = [p for p in required_premises if p not in self.processed_premises]
                if new_premises:
                    if self.process_batch(new_premises, conclusion):
                        self.processed_premises.update(new_premises)
                    else:
                        return
            
            self.type_handler.commit_pending_types()
            
        except Exception as e:
            print(f"Error processing puzzle: {e}")
            self.sentence_handler.pending_rag_entries = []
            self.type_handler.clear_pending_types()
            raise
