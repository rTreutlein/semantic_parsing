from openai import OpenAI
import os
import re
import argparse
from utils.ragclass import RAG
from utils.prompts import nl2pln, fix_opencog_pln

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def extract_opencog_pln(response):
    match = re.search(r'```(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def convert_to_opencog_pln(line, similar):
    completion = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.5,
        messages=[{"role": "user", "content": nl2pln(line, similar)},],
    )
    txt = completion.choices[0].message.content
    return extract_opencog_pln(txt)

def process_sentence(line, rag):
    similar = rag.search_similar(line, limit=5)

    print(f"Processing line: {line}")
    pln = convert_to_opencog_pln(line, similar)

    print(f"OpenCog PLN: {pln}")
    if pln is None:
        return None

    while True:
        user_input = input("Is this conversion correct? (y/n): ").lower()
        if user_input == 'y':
            break
        elif user_input == 'n':
            pln = input("Please provide the correct OpenCog PLN conversion: ")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    rag.store_embedding(f"Sentence: {line}\nOpenCog PLN: {pln}")
    return pln

def process_file(file_path, skip_lines=0, limit_lines=None):
    collection_name = os.path.splitext(os.path.basename(file_path))[0]
    rag = RAG(collection_name=collection_name)
    res = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        end = len(lines) if limit_lines is None else min(skip_lines + limit_lines, len(lines))
        for i, line in enumerate(lines[skip_lines:end], start=skip_lines):
            pln = process_sentence(line.strip(), rag)
            if pln is None:
                break
            with open("data2/opencog_pln.txt", "a") as file:
                file.write(f"{pln}\n")
            res.append(pln)
            print(f"last idx: {i}")
            print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to OpenCog PLN.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    process_file(args.file_path, args.skip, args.limit)
