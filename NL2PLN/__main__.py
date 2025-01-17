import os
import argparse
import dspy
from NL2PLN.nl2pln import NL2PLN
from NL2PLN.utils.verifier import VerifiedPredictor
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.type_similarity import TypeSimilarityHandler
from NL2PLN.utils.common import process_file


class Processor:
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
        
        self.previous_sentences.append(line)
        if len(self.previous_sentences) > 10:
            self.previous_sentences.pop(0)
        
        return True

def configure_lm(model_name: str = 'anthropic/claude-3-5-sonnet-20241022'):
    """Configure the LM for DSPY."""
    lm = dspy.LM(model_name)
    dspy.configure(lm=lm)

def main():
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to OpenCog PLN.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    # Configure LM
    configure_lm()

    # Initialize processor
    output_base = os.path.splitext(os.path.basename(args.file_path))[0]
    processor = Processor(output_base)

    def process_line(line, index):
        print(f"Current Index: {index}")
        return processor.process_sentence(line)

    process_file(args.file_path, process_line, args.skip, args.limit)

if __name__ == "__main__":
    main()
