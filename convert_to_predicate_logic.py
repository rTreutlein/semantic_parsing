import os
import argparse
from utils.common import process_file, create_openai_completion, extract_logic
from utils.prompts import make_explicit, nl2pl, fix_predicatelogic
from utils.checker import HumanCheck, check_predicate_logic
from metta.python_metta_example import MeTTaHandler
from utils.ragclass import RAG

def make_sentence_explicit(line, similar):
    prompt = make_explicit(line, similar)
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    return extract_logic(txt)

def convert_to_predicate_logic(line, similar):
    prompt = nl2pl(line, similar)
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    return extract_logic(txt)

def fix_predicate_logic(line, similar, original_pred_logic, error_message):
    prompt = fix_predicatelogic(line, original_pred_logic, error_message, similar)
    txt = create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5)
    return extract_logic(txt)

metta_handler = MeTTaHandler()

def process_sentence(line, rag_explicit, rag_predicate, index):
    similar_original = rag_explicit.search_similar(line, limit=5)

    print(f"Processing original line: {line}")
    explicit_sentence = make_sentence_explicit(line, similar_original)
    print(f"Explicit sentence: {explicit_sentence}")

    explicit_sentence = HumanCheck(explicit_sentence, line)

    similar_explicit = rag_predicate.search_similar(explicit_sentence, limit=5)

    print(f"Processing explicit line: {explicit_sentence}")
    pred_logic = convert_to_predicate_logic(explicit_sentence, similar_explicit)

    print(f"Logic: {pred_logic}")
    if pred_logic is None:
        return None

    def fix_logic(pred_logic, error_message):
        return fix_predicate_logic(explicit_sentence, similar_explicit, pred_logic, error_message)

    metta = check_predicate_logic(pred_logic, fix_logic)
    if metta is None:
        return None

    print(f"Metta: {metta}")

    metta = HumanCheck(metta, explicit_sentence)

    rag_explicit.store_embedding(f"Original Sentence: {line}\nExplicit Sentence: {explicit_sentence}")
    rag_predicate.store_embedding(f"Explicit Sentence: {explicit_sentence}\nPredicate Logic: {pred_logic}")
    return f"!(add-atom &kb2 (: d{index} {metta}))"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to predicate logic.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    collection_name = os.path.splitext(os.path.basename(args.file_path))[0]
    rag_explicit = RAG(collection_name=f"{collection_name}_explicit")
    rag_predicate = RAG(collection_name=f"{collection_name}_predicate")

    def process_sentence_wrapper(line, index):
        return process_sentence(line, rag_explicit, rag_predicate, index)

    process_file(args.file_path, process_sentence_wrapper, "data2/fol.txt", args.skip, args.limit)

