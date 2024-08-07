import os
import argparse
from utils.common import process_file, create_openai_completion, extract_logic
from utils.prompts import nl2pl, fix_predicatelogic

def convert_to_predicate_logic(line, similar):
    prompt = nl2pl(line, similar)
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    return extract_logic(txt)

def fix_predicate_logic(line, similar, original_pred_logic, error_message):
    prompt = fix_predicatelogic(line, original_pred_logic, error_message, similar)
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    return extract_logic(txt)

def process_sentence(line, rag, index):
    similar = rag.search_similar(line, limit=5)

    print(f"Processing line: {line}")
    pred_logic = convert_to_predicate_logic(line, similar)

    print(f"Logic: {pred_logic}")
    if pred_logic is None:
        return None

    pred_logic = pred_logic.replace("$", "\\$")
    metta = os.popen(f"plparserexe \"{pred_logic}\"").read().strip()

    print(f"Metta: {metta}")

    if metta.startswith("Error:"):
        print("Trying to fix...")
        pred_logic = fix_predicate_logic(line, similar, pred_logic, metta)
        print(f"Fixed Logic: {pred_logic}")
        if pred_logic is None:
            return None
        pred_logic = pred_logic.replace("$", "\\$")
        metta = os.popen(f"plparserexe \"{pred_logic}\"").read().strip()
        print(f"Fixed Metta: {metta}")

    if metta.startswith("Error:"):
        print("Failed to fix...")
        return None

    rag.store_embedding(f"Sentence: {line}\nPredicate Logic: {pred_logic}")
    return f"!(add-atom &kb2 (: d{index} {metta}))"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to predicate logic.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    process_file(args.file_path, process_sentence, "data2/fol.txt", args.skip, args.limit)

