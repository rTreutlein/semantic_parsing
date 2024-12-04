import argparse
from NL2PLN.utils.common import create_openai_completion
from NL2PLN.utils.query_utils import convert_logic_simple
from NL2PLN.utils.prompts import nl2pln, pln2nl
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.ragclass import RAG
import os
import cmd

class KBShell(cmd.Cmd):
    intro = 'Welcome to the Knowledge Base shell. Type help or ? to list commands.\n'
    prompt = 'KB> '

    def __init__(self, kb_file: str, collection_name: str):
        super().__init__()
        self.debug = False
        self.metta_handler = MeTTaHandler(kb_file)
        self.metta_handler.load_kb_from_file()
        self.rag = RAG(collection_name=collection_name)
        self.query_rag = RAG(collection_name=f"{collection_name}_query")
        self.conversation_history = []
        print(f"Loaded knowledge base from {kb_file}")
        print("Type 'exit' to quit")

    def default(self, line: str):
        """Handle any input that isn't a specific command"""
        if line.lower() == 'exit':
            return
        self.process_input(line)

    def do_exit(self, arg):
        """Exit the shell"""
        return True

    def do_debug(self, arg):
        """Toggle debug mode"""
        self.debug = not self.debug
        print(f"Debug mode: {'on' if self.debug else 'off'}")

    def get_similar_examples(self, input_text):
        # Get examples from both RAG databases
        base_similar = self.rag.search_similar(input_text, limit=3)
        query_similar = self.query_rag.search_similar(input_text, limit=2)
        
        # Combine results
        similar = base_similar + query_similar
        
        return [
            f"Sentence: {item['sentence']}\n"
            f"From Context:\n{'\n'.join(item.get('from_context', []))}\n"
            f"Type Definitions:\n{'\n'.join(item.get('type_definitions', []))}\n"
            f"Statements:\n{'\n'.join(item.get('statements', []))}" 
            for item in similar if 'sentence' in item
        ]

    def get_llm_response(self, user_input: str) -> str:
        """Get response from LLM considering conversation history"""
        messages = []
        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": "user", "content": msg["user"]})
            if msg.get("assistant"):
                messages.append({"role": "assistant", "content": msg["assistant"]})
        
        # Add current input
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response
        response = create_openai_completion("",messages) #System message is empty
        return response

    def process_input(self, user_input: str):
        try:
            # Get LLM response first
            print("\n=== LLM Response ===")
            llm_response = self.get_llm_response(user_input)
            print(llm_response)
            
            # Update conversation history
            self.conversation_history.append({
                "user": user_input,
                "assistant": llm_response
            })

            print("\n=== System Response ===")
            if self.debug: print(f"Processing input: {user_input}")
            similar_examples = self.get_similar_examples(user_input)
            if self.debug: print(f"Similar examples:\n{similar_examples}")
            pln_data = convert_logic_simple(user_input, nl2pln, similar_examples)
            if self.debug:
                print(f"\nConverted PLN data: {pln_data}")
            
            if pln_data == "Performative":
                print("This is a performative statement, not a query or statement.")
                return


            if pln_data["statements"]:
                print("Processing as statement (forward chaining)")
                fc_results = []
                for statement in pln_data["statements"]:
                    # Store the statement in query RAG
                    self.query_rag.store_embedding({
                        "sentence": user_input,
                        "statements": [statement],
                        "type_definitions": pln_data.get("type_definitions", []),
                        "from_context": []
                    })
                    result = self.metta_handler.add_atom_and_run_fc(statement)
                    if result:
                        fc_results.extend(result)
                
                if fc_results and self.debug:
                    print(f"FC results: {fc_results}")
                    print("\nInferred results:")
                    for result in fc_results:
                        english = convert_logic_simple(result, pln2nl, similar_examples)
                        print(f"- {english}")
                else:
                    print("No new inferences made.")

            if pln_data["questions"]:
                print("Processing as query (backward chaining)")
                metta_results = self.metta_handler.bc(pln_data["questions"][0])
                if self.debug: print("metta_results:" + metta_results)
                for result in metta_results:
                    english = convert_logic_simple(result, pln2nl, similar_examples)
                    print(f"- {english}")


        except Exception as e:
            print(f"Error processing input: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Interactive shell for querying the knowledge base.")
    parser.add_argument("kb_file", help="Path to the knowledge base file (.metta)")
    args = parser.parse_args()

    collection_name = os.path.splitext(os.path.splitext(os.path.basename(args.kb_file))[0])[0]
    KBShell(args.kb_file, f"{collection_name}_pln").cmdloop()

if __name__ == "__main__":
    main()
