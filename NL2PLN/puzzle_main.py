import argparse
import dspy
from NL2PLN.utils.query_utils import convert_to_english
from NL2PLN.nl2pln import NL2PLN
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.checker import human_verify_prediction
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator
from NL2PLN.tests.example_puzzle import ExamplePuzzleGenerator
from NL2PLN.utils.type_similarity import TypeSimilarityHandler


def nl2plnVerified(input_text, nl2pln, previous_sentences=None):
    prediction = nl2pln.forward(input_text, previous_sentences)
    validated_data = human_verify_prediction(prediction, input_text)
    return validated_data

def run_forward_chaining(metta_handler, pln):
    fc_results = metta_handler.add_atom_and_run_fc(pln)
    print(f"Forward chaining results: {fc_results}")
    return fc_results

def process_forward_chaining_results(rag, fc_results, pln, similar_examples):
    print("Fix conversion to english by checking if the generated statement is intersting.")
    return 

    english_results = [convert_to_english(result, "", similar_examples) for result in fc_results]
    print(f"Forward chaining results in English: {english_results}")

    for fc_result, english_result in zip(fc_results, english_results):
        rag.store_embedding({
            "sentence": english_result,
            "statements": fc_result,
            "from_context": [],  # Forward chaining results don't have from context
            "type_definitions": [],  # Forward chaining results don't have type definitions
        }, ["sentence","statements"])

    return

def store_results(rag, sentence, pln_data):
    rag.store_embedding({
        "sentence": sentence,
        "from_context": pln_data["from_context"],
        "type_definitions": pln_data["type_definitions"],
        "statements": pln_data["statements"]
    }, ["sentence","statements"])


def process_sentence(line, nl2pln, metta_handler, type_handler, previous_sentences=None) -> bool:
    previous_sentences = previous_sentences or []

    print(f"Processing line: {line}")
    pln_data = nl2plnVerified(line, nl2pln, previous_sentences)
    if pln_data.statements[0] == "Performative":
        return True
    
    # Process type definitions first
    linking_statements = type_handler.process_new_typedefs(pln_data.typedefs)
    print(f"Found {len(linking_statements)} linking statements")
    print(linking_statements)
    
    # Add type definitions and any discovered type relationships to MeTTa KB
    for type_def in pln_data.typedefs:
        conflict = metta_handler.add_to_context(type_def)
        if isinstance(conflict, str):
            print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
            input("Press Enter to continue...")
            return False
            
    # Add any discovered type relationships
    for linking_stmt in linking_statements:
        conflict = metta_handler.add_to_context(linking_stmt)
        if isinstance(conflict, str):
            print(f"WARNING: Type relationship {linking_stmt} conflicts with existing atom: {conflict}")
    
    # Then add and process all statements
    store_results(rag, line, pln_data)
    
    # Run forward chaining on each statement
    fc_results = []
    for statement in pln_data.statements:
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

    # Initialize RAG and TypeSimilarityHandler
    rag = RAG(collection_name=f"{args.output}_pln",reset_db=args.example)
    type_handler = TypeSimilarityHandler(collection_name=f"{args.output}_types")


    # Initialize DSPY LM
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
    dspy.configure(lm=lm)

    nl2pln = NL2PLN(rag)

    previous_sentences = []
    for i in range(args.num_puzzles):
        print(f"\nGenerating puzzle {i+1}/{args.num_puzzles}")
        puzzle_sections = puzzle_gen.generate_puzzle()
        print(puzzle_sections)
        
        def process_section(section_name, sentences):
            print(f"\nProcessing {section_name}:")
            for sentence in sentences:
                if sentence.strip():
                   result = process_sentence(sentence, nl2pln, metta_handler, type_handler,
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
            pln_data = nl2plnVerified("Is it true that " + conclusion, nl2pln, previous_sentences)
            if pln_data != "Performative":
                print(f"\nAttempting to prove conclusion: {conclusion}")
                for query in pln_data["questions"]:
                    proof_steps, proven = metta_handler.bc(query)
                    print(f"\nConclusion statement: {query}")
                    print(f"Proven: {proven}")
                    if proof_steps:
                        print("Proof steps:")
                        for step in proof_steps:
                            print(f"  {step}")

if __name__ == "__main__":
    main()
