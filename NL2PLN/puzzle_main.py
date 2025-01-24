import argparse
import random
import dspy
from sammo import Data
from NL2PLN.utils.proof_assistant import ProofAssistant, _parse_suggestion
from NL2PLN.utils.query_utils import convert_to_english
from NL2PLN.nl2pln import NL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator
from NL2PLN.tests.example_puzzle import ExamplePuzzleGenerator
from NL2PLN.utils.type_similarity import TypeSimilarityHandler

class PuzzleProcessor:
    def __init__(self, output_base: str, reset_db: bool = False, verify: bool = False):
        self.output_base = output_base
        self.previous_sentences = []
        self.processed_premises = set()
        self.pending_rag_entries = []
        self.pending_statements = []
        self.puzzle_counter = 0
        self.proof_assistant = ProofAssistant(llm_runner=dspy.settings.lm)
        
        # Initialize components
        self.output_base = output_base
        self.metta_handler = None
        self.rag = RAG(collection_name=f"{output_base}_pln", reset_db=reset_db)
        self.type_handler = TypeSimilarityHandler(collection_name=f"{output_base}_types", reset_db=reset_db, verify=verify)
        
        if verify:
            self.nl2pln = VerifiedPredictor(
                predictor=NL2PLN(self.rag),
                verify_func=human_verify_prediction,
                cache_file=f"{output_base}_verified_nl2pln.json"
            )
        else:
            self.nl2pln = NL2PLN(self.rag)

    def store_sentence_results(self, sentence: str, pln_data: dspy.Prediction):
        """Store processed sentence results in RAG."""
        self.rag.store_embedding({
            "sentence": sentence,
            "from_context": pln_data.context,
            "type_definitions": pln_data.typedefs,
            "statements": pln_data.statements,
        }, embedding_fields=["sentence", "statements"])

    def process_type_definitions(self, pln_data) -> bool:
        """Process and validate type definitions."""
        
        # Add type definitions
        for type_def in pln_data.typedefs:
            conflict = self.metta_handler.add_to_context(type_def)
            if isinstance(conflict, str):
                print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
                input("Press Enter to continue...")
                return False
                
        linking_statements = self.type_handler.stage_new_typedefs(pln_data.typedefs)
        print(f"Found {len(linking_statements)} linking statements")
        print(linking_statements)

        # Add type relationships
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
            
        # Save for later storage if proof succeeds
        self.pending_rag_entries.append((line, pln_data))
        
        self.pending_statements.append(pln_data.statements)
        
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

    def process_conclusion(self, conclusion: str):
        """Process and verify the conclusion."""
        if not conclusion.strip():
            return
            
        print("\nProcessing conclusion:")
        recent_context = self.previous_sentences[-10:] if self.previous_sentences else []
        pln_data = self.nl2pln("Is it true that " + conclusion, previous_sentences=recent_context)
        print(pln_data)
        
        if pln_data == "Performative":
            return

        if len(pln_data.questions) > 1:
            print(f"Error expection only a single question")
            return

        if (not self.try_to_proof(pln_data.questions[0])):
            self.handle_failed_conclusion(pln_data.questions[0])
            
        self.pending_statements = []
        for sentence, pln_data in self.pending_rag_entries:
            self.store_sentence_results(sentence, pln_data)
        self.pending_rag_entries = []

        return False

    def try_to_proof(self, conclusion):
        for statement in self.pending_statements:
            self.metta_handler.add_atom_and_run_fc(statement)

        proof_steps, proven = self.metta_handler.bc(query)
        return proven


    def handle_failed_conclusion(self, conclusion):
        """Handle a failed proof attempt using SAMMO proof assistant."""
        # SAMMO data preparation
        input_data = Data.from_dict({
            "premises_english": premises,
            "premises_pln": [s for _, data in self.pending_rag_entries for s in data.statements],
            "conclusion_english": conclusion,
            "conclusion_pln": pln_statements,
            "existing_proof_steps": proof_steps
        })
        
        # Get structured suggestion
        raw_suggestion = self.proof_assistant.analyze_failure(input_data)
        suggestion = _parse_suggestion(raw_suggestion)
        
        # Rest of the handling remains the same
        if suggestion["action"] == "fix_premise":
            return self.retry_fixed_premise(suggestion)
        elif suggestion["action"] == "combine_statements":
            return self.try_combination(suggestion)
        else:
            return human_verify_prediction(...)

    def process_puzzle(self, puzzle_sections: dict):
        """Process a complete puzzle."""
        print(puzzle_sections)
        
        # Create new MeTTaHandler for this puzzle with unique file name
        if self.metta_handler:
            self.metta_handler = None  # Allow previous handler to be garbage collected
        
        self.puzzle_counter += 1    
        self.metta_handler = MeTTaHandler(f"{self.output_base}_{self.puzzle_counter}.metta")
        self.metta_handler.load_kb_from_file()
        
        deductions = puzzle_sections.get('deduction', [])
        
        try:
            # Process each deduction step
            for required_premises, conclusion in deductions:
                # Only process premises we haven't seen yet
                new_premises = [p for p in required_premises if p not in self.processed_premises]
                if new_premises:
                    if not self.process_section("premises", new_premises):
                        print("Failed to process premises, stopping early")
                        print(f"Premises: {new_premises}")
                        self.type_handler.clear_pending_types()
                        return
                    self.processed_premises.update(new_premises)
                
                # Try to prove the conclusion
                if not self.process_conclusion(conclusion):
                    print("Failed to prove conclusion, discarding pending entries")
                    print(f"Conclusion: {conclusion}")
                    self.pending_rag_entries = []
                    self.type_handler.clear_pending_types()
                    return
            
            # If we get here, puzzle succeeded - commit everything
            self.type_handler.commit_pending_types()
            
        except Exception as e:
            print(f"Error processing puzzle: {e}")
            self.pending_rag_entries = []
            self.type_handler.clear_pending_types()
            raise

def configure_lm(model_name: str = 'anthropic/claude-3-5-sonnet-20241022'):
    """Configure the LM for DSPY."""
    lm = dspy.LM(model_name)
    dspy.configure(lm=lm)

def main():
    parser = argparse.ArgumentParser(description="Generate and process logic puzzles using OpenCog PLN.")
    parser.add_argument("--output", default="puzzle", help="Base name for output files")
    parser.add_argument("--num-puzzles", type=int, default=1, help="Number of puzzles to generate")
    parser.add_argument("--example", action="store_true", help="Run the example puzzle")
    parser.add_argument("--verify", action="store_true", help="Verify the NL2PLN module")
    args = parser.parse_args()

    # Configure LM
    configure_lm()

    # Initialize puzzle generator and processor
    puzzle_gen = ExamplePuzzleGenerator() if args.example else LogicPuzzleGenerator()
    processor = PuzzleProcessor(args.output, reset_db=args.example, verify=args.verify)
    
    for i in range(args.num_puzzles):
        print(f"\nGenerating puzzle {i+1}/{args.num_puzzles}")
        puzzle = puzzle_gen.generate_puzzle(numberOfPremises=2)
        processor.process_puzzle(puzzle)

if __name__ == "__main__":
    main()
