from openai import OpenAI
import os
import re
from utils.ragclass import RAG

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def extract_logic(response):
    match = re.search(r'```(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def process_file(file_path, process_sentence_func, output_file, skip_lines=0, limit_lines=None):
    res = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        end = len(lines) if limit_lines is None else min(skip_lines + limit_lines, len(lines))
        for i, line in enumerate(lines[skip_lines:end], start=skip_lines):
            result = process_sentence_func(line.strip(), i)
            if result is None:
                break
            with open(output_file, "a") as out_file:
                out_file.write(f"{result}\n")
            res.append(result)
            print(f"last idx: {i}")
            print("--------------------------------------------------------------------------------")
    return res

def create_openai_completion(prompt, model="openai/gpt-4o-2024-08-06", temperature=0.5):
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    if not completion.choices:
        print(completion)
        raise Exception("OpenAI API returned no choices")
    return completion.choices[0].message.content
