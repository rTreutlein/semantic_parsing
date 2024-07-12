from openai import OpenAI
import os
import re
import argparse
from ragclass import RAG
import os
from prompts import nl2pl, fix_predicatelogic
from filter_pl import check_predicates

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def extract_predicate_logic(response):
    match = re.search(r'```(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def convert_to_predicate_logic(line,simiarl): 

    completion = client.chat.completions.create(
        #model="meta-llama/llama-3-70b-instruct",
        #model="openai/gpt-4o",
        model="anthropic/claude-3.5-sonnet",
        #model="microsoft/wizardlm-2-8x22b",
        temperature=0.5,
        messages=[ {"role": "user","content": nl2pl(line,simiarl), },],
    )
    txt = completion.choices[0].message.content
    return extract_predicate_logic(txt)

def fix_predicate_logic(line, similar, original_pred_logic, error_message):
    completion = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.5,
        messages=[
            {"role": "user", "content": fix_predicatelogic(line, original_pred_logic, error_message, similar)},
        ],
    )
    txt = completion.choices[0].message.content
    return extract_predicate_logic(txt)

def process_file(file_path, skip_lines=0, limit_lines=float('inf')):
    collection_name = os.path.splitext(os.path.basename(file_path))[0]
    rag = RAG(collection_name=collection_name)
    res = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines[skip_lines:skip_lines+limit_lines]):
            line = line.strip()
            print(f"Processing line: {line}")
            similar = rag.search_similar(line, limit=5)
            pred_logic = convert_to_predicate_logic(line,similar)

            print(f"Logic: {pred_logic}")
            if pred_logic is None:
                break

            #call shell command plparserexe and capture its output
            metta = os.popen(f"plparserexe \"{pred_logic.replace('$','\\$')}\"").read().strip()

            print(f"Metta: {metta}")

            if metta.startswith("Error:"):
                print("Trying to fix...")
                pred_logic = fix_predicate_logic(line, similar, pred_logic, metta)
                print(f"Fixed Logic: {pred_logic}")
                if pred_logic is None:
                    break
                metta = os.popen(f"plparserexe \"{pred_logic.replace('$','\\$')}\"").read().strip()
                print(f"Fixed Metta: {metta}")

            if metta.startswith("Error:"):
                print("Failed to fix...")
                break

            is_trivial, _ = check_predicates(metta)
            if is_trivial:
                print("Skipping trivial metta statement.")
                continue

            res.append(metta)
            rag.store_embedding(f"Sentence: {line}\nPredicate Logic: {pred_logic}")
            with open("data/fol.txt","a") as file:
                file.write("!(add-atom &kb2 (: d"+ str(i+skip_lines) + " " + metta + "))\n")
            print("last idx: " + str(i + skip_lines))
            print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to predicate logic.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    process_file(args.file_path, args.skip, args.limit)


