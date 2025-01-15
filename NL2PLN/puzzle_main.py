import argparse
import dspy
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
    def __init__(self, output_base: str, reset_db: bool = False):
        self.output_base = output_base
        self.previous_sentences = []
        
        # Initialize components
        self.metta_handler = MeTTaHandler(f"{output_base}.metta")
        self.metta_handler.load_kb_from_file()
        
        self.rag = RAG(collection_name=f"{output_base}_pln", reset_db=reset_db)
        self.type_handler = TypeSimilarityHandler(collection_name=f"{output_base}_types", reset_db=reset_db)
        
        self.nl2pln = VerifiedPredictor(
            predictor=NL2PLN(self.rag),
            verify_func=human_verify_prediction,
            cache_file=f"{output_base}_verified_nl2pln.json"
        )

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
                
        linking_statements = self.type_handler.process_new_typedefs(pln_data.typedefs)
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
        pln_data = self.nl2pln.predict(line, previous_sentences=recent_context)
        
        if pln_data.statements[0] == "Performative":
            return True
            
        if not self.process_type_definitions(pln_data):
            return False
            
        self.store_sentence_results(line, pln_data)
        
        # Process forward chaining
        for statement in pln_data.statements:
            fc_results = self.metta_handler.add_atom_and_run_fc(statement)
            if fc_results:
                print(f"Forward chaining results: {fc_results}")
                print("Fix conversion to english by checking if the generated statement is interesting.")
        
        self.previous_sentences.append(line)
        if len(self.previous_sentences) > 10:
            self.previous_sentences.pop(0)
        
        return True

    def process_section(self, section_name: str, sentences: list[str]):
        """Process a section of sentences."""
        print(f"\nProcessing {section_name}:")
        for sentence in sentences:
            if sentence.strip():
                self.process_sentence(sentence)

    def process_conclusion(self, conclusion: str):
        """Process and verify the conclusion."""
        if not conclusion.strip():
            return
            
        print("\nProcessing conclusion:")
        recent_context = self.previous_sentences[-10:] if self.previous_sentences else []
        pln_data = self.nl2pln.predict("Is it true that " + conclusion, previous_sentences=recent_context)
        
        if pln_data == "Performative":
            return
            
        print(f"\nAttempting to prove conclusion: {conclusion}")
        for query in pln_data.questions:
            proof_steps, proven = self.metta_handler.bc(query)
            print(f"\nConclusion statement: {query}")
            print(f"Proven: {proven}")
            if proof_steps:
                print("Proof steps:")
                for step in proof_steps:
                    print(f"  {step}")

    def process_puzzle(self, puzzle_sections: dict):
        """Process a complete puzzle."""
        print(puzzle_sections)
        
        # Process sections in order
        self.process_section("common sense knowledge", 
                           puzzle_sections.get('common_sense', '').split('\n'))
        self.process_section("premises", 
                           puzzle_sections.get('premises', '').split('\n'))
        self.process_conclusion(puzzle_sections.get('conclusion', ''))

def configure_lm(model_name: str = 'anthropic/claude-3-5-sonnet-20241022'):
    """Configure the LM for DSPY."""
    lm = dspy.LM(model_name)
    dspy.configure(lm=lm)

def main():
    parser = argparse.ArgumentParser(description="Generate and process logic puzzles using OpenCog PLN.")
    parser.add_argument("--output", default="puzzle", help="Base name for output files")
    parser.add_argument("--num-puzzles", type=int, default=1, help="Number of puzzles to generate")
    parser.add_argument("--example", action="store_true", help="Run the example puzzle")
    args = parser.parse_args()

    # Configure LM
    configure_lm()

    # Initialize puzzle generator and processor
    puzzle_gen = ExamplePuzzleGenerator() if args.example else LogicPuzzleGenerator()
    processor = PuzzleProcessor(args.output, reset_db=args.example)
    
    for i in range(args.num_puzzles):
        print(f"\nGenerating puzzle {i+1}/{args.num_puzzles}")
        puzzle = puzzle_gen.generate_puzzle()
        processor.process_puzzle(puzzle)

if __name__ == "__main__":
    main()
