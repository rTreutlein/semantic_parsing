import argparse
from utils.common import process_file, create_openai_completion, extract_logic
from utils.prompts import nl2pln
from metta.python_metta_example import MeTTaHandler
from utils.checker import HumanCheck

metta_handler = MeTTaHandler()

def convert_to_opencog_pln(line, similar):
    prompt = nl2pln(line, similar)
    print("--------------------------------------------------------------------------------")
    print(f"Prompt: {prompt}")
    
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    print("--------------------------------------------------------------------------------")
    print("LLM output:")
    print(txt)
    return extract_logic(txt)

def process_sentence(line, rag, index):
    similar = rag.search_similar(line, limit=5)

    print(f"Processing line: {line}")
    pln = convert_to_opencog_pln(line, similar)

    print("--------------------------------------------------------------------------------")
    print(f"Sentence: {line}")
    print(f"OpenCog PLN: {pln}")
    if pln is None:
        return None

    pln = HumanCheck(pln, line)

    rag.store_embedding(f"Sentence:\n{line}\nOpenCog PLN:\n{pln}")
    
    # Add the PLN statement to MeTTa and run forward chaining
    fc_result = metta_handler.add_atom_and_run_fc(pln)
    print(f"Forward chaining result: {fc_result}")
    
    return pln

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to OpenCog PLN.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    process_file(args.file_path, process_sentence, "data2/opencog_pln.txt", args.skip, args.limit)
