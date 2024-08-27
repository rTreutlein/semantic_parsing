import argparse
from utils.common import process_file, create_openai_completion, extract_logic
from utils.prompts import nl2pln, pln2nl
from metta.python_metta_example import MeTTaHandler
from utils.checker import HumanCheck
from utils.ragclass import RAG
import os

metta_handler = MeTTaHandler()

def convert_to_opencog_pln(line, similar_examples):
    prompt = nl2pln(line, similar_examples)
    print("--------------------------------------------------------------------------------")
    print(f"Prompt: {prompt}")
    
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    print("--------------------------------------------------------------------------------")
    print("LLM output:")
    print(txt)
    return extract_logic(txt)

def convert_pln_to_english(pln):
    prompt = pln2nl(pln)
    print("--------------------------------------------------------------------------------")
    print(f"PLN to NL Prompt: {prompt}")
    
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    print("--------------------------------------------------------------------------------")
    print("PLN to NL LLM output:")
    print(txt)
    
    # Extract the converted sentence from within the backticks
    converted_sentence = txt.strip()
    if converted_sentence.startswith("```") and converted_sentence.endswith("```"):
        converted_sentence = converted_sentence[3:-3].strip()
    return converted_sentence

def process_sentence(line, rag):
    similar = rag.search_similar(line, limit=5)
    similar_examples = [f"Sentence: {item['sentence']}\nPLN: {item['pln']}" for item in similar if 'sentence' in item and 'pln' in item]

    print(f"Processing line: {line}")
    pln = convert_to_opencog_pln(line, similar_examples)

    print("--------------------------------------------------------------------------------")
    print(f"Sentence: {line}")
    print(f"OpenCog PLN: {pln}")
    if pln is None:
        return None

    pln = HumanCheck(pln, line)

    rag.store_embedding({
        "sentence": line,
        "pln": pln
    })
    
    # Add the PLN statement to MeTTa and run forward chaining
    fc_results = metta_handler.add_atom_and_run_fc(pln)
    print(f"Forward chaining results: {fc_results}")
    
    if fc_results:
        english_results = [convert_pln_to_english(result) for result in fc_results]
        print(f"Forward chaining results in English: {english_results}")
        
        # Store each forward chaining result separately
        for fc_result, english_result in zip(fc_results, english_results):
            rag.store_embedding({
                "sentence": english_result,
                "pln": fc_result
            })
        
        return pln, fc_results, english_results
    
    return pln, None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to OpenCog PLN.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    collection_name = os.path.splitext(os.path.basename(args.file_path))[0]
    rag=RAG(collection_name=f"{collection_name}_pln")

    def process_sentence_wrapper(line, index):
        if index < args.skip:
            # Retrieve PLN from RAG database and add to MeTTa
            similar = rag.search_exact(line)
            if similar:
                pln = similar['pln']
                print(pln)
                fc_results = metta_handler.add_atom_and_run_fc(pln)
                print(f"Forward chaining results: {fc_results}",flush=True)
                if fc_results:
                    english_results = [convert_pln_to_english(result) for result in fc_results]
                    print(f"Forward chaining results in English: {english_results}")
                    
                    # Store each forward chaining result separately
                    for fc_result, english_result in zip(fc_results, english_results):
                        rag.store_embedding({
                            "sentence": english_result,
                            "pln": fc_result
                        })
                    
                    return pln, fc_results, english_results
                return pln, None, None
        else:
            input("Checkpoint")
            return process_sentence(line, rag)

    process_file(args.file_path, process_sentence_wrapper, "data2/opencog_pln.txt", args.skip, args.limit)
