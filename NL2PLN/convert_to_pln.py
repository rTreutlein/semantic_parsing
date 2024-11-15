import argparse
from utils.common import process_file, create_openai_completion, extract_logic
from utils.prompts import nl2pln, pln2nl
from metta.metta_handler import MeTTaHandler
from utils.checker import HumanCheck
from utils.ragclass import RAG
import os


def convert_logic(input_text, prompt_func, similar_examples):
    prompt = prompt_func(input_text, similar_examples)
    print("--------------------------------------------------------------------------------")
    print(f"Prompt: {prompt}")
    
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
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

def run_forward_chaining(pln):
    fc_results = metta_handler.add_atom_and_run_fc(pln)
    print(f"Forward chaining results: {fc_results}")
    return fc_results

def process_forward_chaining_results(fc_results, pln, similar_examples):
    english_results = [convert_logic(result, pln2nl, similar_examples) for result in fc_results]
    print(f"Forward chaining results in English: {english_results}")
    store_fc_results(fc_results, english_results)
    return pln, fc_results, english_results

def store_results(rag, sentence, pln_data):
    rag.store_embedding({
        "sentence": sentence,
        "type_definitions": pln_data["type_definitions"],
        "statements": pln_data["statements"]
    })

def store_fc_results(fc_results, english_results):
    for fc_result, english_result in zip(fc_results, english_results):
        rag.store_embedding({
            "sentence": english_result,
            "pln": fc_result,
            "preconditions": []  # Forward chaining results don't have preconditions
        })

def process_sentence(line, rag) -> bool:
    similar = rag.search_similar(line, limit=5)
    similar_examples = [f"Sentence: {item['sentence']}\nType Definitions:\n{'\n'.join(item.get('type_definitions', []))}\nStatements:\n{'\n'.join(item.get('statements', []))}" 
                       for item in similar if 'sentence' in item]

    print(f"Processing line: {line}")
    pln_data = convert_logic(line, nl2pln, similar_examples)
    if pln_data == "Performative":
        return True
    
    # Add type definitions to MeTTa KB first
    for type_def in pln_data["type_definitions"]:
        conflict = metta_handler.add_to_context(type_def)
        if isinstance(conflict, str):
            print(f"ERROR: Conflict detected! Type definition {type_def} conflicts with existing atom: {conflict}")
            return False
    
    # Then add and process all statements
    store_results(rag, line, pln_data)
    
    # Run forward chaining on each statement
    fc_results = []
    for statement in pln_data["statements"]:
        fc_result = run_forward_chaining(statement)
        if fc_result:
            fc_results.extend(fc_result)
    if fc_results:
        process_forward_chaining_results(fc_results, pln_data, similar_examples)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to OpenCog PLN.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    metta_handler = MeTTaHandler(args.file_path + ".metta")
    metta_handler.load_kb_from_file()
    print("Loaded kb:")
    print(metta_handler.run("!(kb)"))

    collection_name = os.path.splitext(os.path.basename(args.file_path))[0]
    rag=RAG(collection_name=f"{collection_name}_pln")

    def process_sentence_wrapper(line, index):
        print(f"Current Index: {index}")
        return process_sentence(line, rag)

    process_file(args.file_path, process_sentence_wrapper, args.skip, args.limit)
