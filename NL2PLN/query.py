import argparse
from NL2PLN.utils.common import create_openai_completion, extract_logic
from NL2PLN.__main__ import convert_logic
from NL2PLN.utils.prompts import nl2pln, pln2nl
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.query_utils import is_question
import os
import cmd

class KBShell(cmd.Cmd):
    intro = 'Welcome to the Knowledge Base shell. Type help or ? to list commands.\n'
    prompt = 'KB> '

    def __init__(self, kb_file: str, collection_name: str):
        super().__init__()
        self.metta_handler = MeTTaHandler(kb_file)
        self.metta_handler.load_kb_from_file()
        self.rag = RAG(collection_name=collection_name)
        print(f"Loaded knowledge base from {kb_file}")
        print("Type 'exit' to quit")

    def default(self, line: str):
        """Handle any input that isn't a specific command"""
        if line.lower() == 'exit':
            return True
        self.process_input(line)

    def do_exit(self, arg):
        """Exit the shell"""
        return True

    def get_similar_examples(self, input_text):
        similar = self.rag.search_similar(input_text, limit=5)
        return [
            f"Sentence: {item['sentence']}\n"
            f"From Context:\n{'\n'.join(item.get('from_context', []))}\n"
            f"Type Definitions:\n{'\n'.join(item.get('type_definitions', []))}\n"
            f"Statements:\n{'\n'.join(item.get('statements', []))}" 
            for item in similar if 'sentence' in item
        ]

    def process_input(self, user_input: str):
        try:
            similar_examples = self.get_similar_examples(user_input)
            pln_data = convert_logic(user_input, nl2pln, similar_examples)
            
            if pln_data == "Performative":
                print("This is a performative statement, not a query or statement.")
                return

            if is_question(user_input):
                print("Processing as question (backward chaining) - Not implemented yet")
                # TODO: Implement backward chaining once added to metta_handler
                print("Backward chaining not implemented yet")
            else:
                print("Processing as statement (forward chaining)")
                fc_results = []
                for statement in pln_data["statements"]:
                    result = self.metta_handler.add_atom_and_run_fc(statement)
                    if result:
                        fc_results.extend(result)
                
                if fc_results:
                    print("\nInferred results:")
                    for result in fc_results:
                        english = convert_logic(result, pln2nl, similar_examples)
                        print(f"- {english}")
                else:
                    print("No new inferences made.")

        except Exception as e:
            print(f"Error processing input: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Interactive shell for querying the knowledge base.")
    parser.add_argument("kb_file", help="Path to the knowledge base file (.metta)")
    args = parser.parse_args()

    collection_name = os.path.splitext(os.path.basename(args.kb_file))[0]
    KBShell(args.kb_file, f"{collection_name}_pln").cmdloop()

if __name__ == "__main__":
    main()
