import argparse
import os
from NL2PLN.utils.common import create_openai_completion, extract_logic
from NL2PLN.utils.query_utils import convert_to_english
from NL2PLN.utils.prompts import nl2pln, pln2nl
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import HumanCheck
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator
from NL2PLN.tests.example_puzzle import ExamplePuzzleGenerator

def convert_logic(input_text, prompt_func, similar_examples, previous_sentences=None):
    system_msg, user_msg = prompt_func(input_text, similar_examples, previous_sentences or [])
    txt = create_openai_completion(system_msg, user_msg)
    print("--------------------------------------------------------------------------------")
    print("LLM output:")
    print(txt)
    logic_data = extract_logic(txt)

    if logic_data is None:
        raise RuntimeError("No output from LLM")

    # Validate the entire output at once
    validated_data = HumanCheck(txt, input_text)
    logic_data = extract_logic(validated_data)
    
    if logic_data is None:
        raise RuntimeError("No output from validation")
        
    return logic_data

def run_forward_chaining(metta_handler, pln):
    fc_results = metta_handler.add_atom_and_run_fc(pln)
    print(f"Forward chaining results: {fc_results}")
    return fc_results

def process_forward_chaining_results(rag, fc_results, pln, similar_examples):
    english_results = [convert_to_english(result, "", similar_examples) for result in fc_results]
    print(f"Forward chaining results in English: {english_results}")
    store_fc_results(rag, fc_results, english_results)
    return pln, fc_results, english_results

def store_results(rag, sentence, pln_data):
    rag.store_embedding({
        "sentence": sentence,
        "from_context": pln_data["from_context"],
        "type_definitions": pln_data["type_definitions"],
        "statements": pln_data["statements"]
    })

def store_fc_results(rag, fc_results, english_results):
    for fc_result, english_result in zip(fc_results, english_results):
        rag.store_embedding({
            "sentence": english_result,
            "statements": fc_result,
            "from_context": [],  # Forward chaining results don't have from context
            "type_definitions": [],  # Forward chaining results don't have type definitions
        })

def process_sentence(line, rag, metta_handler, previous_sentences=None) -> bool:
    similar = rag.search_similar(line, limit=5)
    previous_sentences = previous_sentences or []
    similar_examples = [f"Sentence: {item['sentence']}\nFrom Context:\n{'\n'.join(item.get('from_context', []))}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}" 
                       for item in similar if 'sentence' in item]

    print(f"Processing line: {line}")
    pln_data = convert_logic(line, nl2pln, similar_examples, previous_sentences)
    if pln_data == "Performative":
        return True
    
    # Add type definitions to MeTTa KB first
    for type_def in pln_data["type_definitions"]:
        conflict = metta_handler.add_to_context(type_def)
        if isinstance(conflict, str):
            print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
            input("Press Enter to continue...")
            return False
    
    # Then add and process all statements
    store_results(rag, line, pln_data)
    
    # Run forward chaining on each statement
    fc_results = []
    for statement in pln_data["statements"]:
        fc_result = run_forward_chaining(metta_handler, statement)
        if fc_result:
            fc_results.extend(fc_result)
    if fc_results:
        process_forward_chaining_results(rag, fc_results, pln_data, similar_examples)
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate and process logic puzzles using OpenCog PLN.")
    parser.add_argument("--output", default="puzzle", help="Base name for output files")
    parser.add_argument("--num-puzzles", type=int, default=1, help="Number of puzzles to generate")
    parser.add_argument("--example", action="store_true", help="Run the example puzzle")
    args = parser.parse_args()

    # Initialize puzzle generator
    if args.example:
        puzzle_gen = ExamplePuzzleGenerator()
    else:
        puzzle_gen = LogicPuzzleGenerator()
    
    # Initialize MeTTa handler
    metta_handler = MeTTaHandler(f"{args.output}.metta")
    metta_handler.load_kb_from_file()
    print("Loaded kb:")
    print(metta_handler.run("!(kb)"))

    # Initialize RAG
    rag = RAG(collection_name=f"{args.output}_pln")

    previous_sentences = []
    for i in range(args.num_puzzles):
        print(f"\nGenerating puzzle {i+1}/{args.num_puzzles}")
        puzzle_sections = puzzle_gen.generate_puzzle()
        print(puzzle_sections)
        
        def process_section(section_name, sentences):
            print(f"\nProcessing {section_name}:")
            for sentence in sentences:
                if sentence.strip():
                   result = process_sentence(sentence, rag, metta_handler, 
                                          previous_sentences[-10:] if previous_sentences else [])
                   if result:
                       previous_sentences.append(sentence)
                       if len(previous_sentences) > 10:
                           previous_sentences.pop(0)

        # Process common sense knowledge first
        process_section("common sense knowledge", puzzle_sections.get('common_sense', '').split('\n'))

        # Process premises next
        process_section("premises", puzzle_sections.get('premises', '').split('\n'))
        
        # Process conclusion using backward chaining
        print("\nProcessing conclusion:")
        conclusion = puzzle_sections.get('conclusion', '').strip()
        if conclusion:
            similar = rag.search_similar(conclusion, limit=5)
            similar_examples = [f"Sentence: {item['sentence']}\nFrom Context:\n{'\n'.join(item.get('from_context', []))}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}" 
                              for item in similar if 'sentence' in item]
            
            pln_data = convert_logic(conclusion, nl2pln, similar_examples, previous_sentences)
            if pln_data != "Performative":
                print(f"\nAttempting to prove conclusion: {conclusion}")
                for statement in pln_data["statements"]:
                    proof_steps, proven = metta_handler.bc(statement)
                    print(f"\nConclusion statement: {statement}")
                    print(f"Proven: {proven}")
                    if proof_steps:
                        print("Proof steps:")
                        for step in proof_steps:
                            print(f"  {step}")

if __name__ == "__main__":
    main()
