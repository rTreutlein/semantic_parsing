from openai import OpenAI
import os
import re
import argparse
from rag import store_embedding_in_qdrant, ensure_predicates_collection, search_similar_predicates

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

def format_prompt(sentence,similar):
    return f"""
You are tasked with converting a sentence to first-order predicate logic. Here is the sentence:

<sentence>
{sentence}
</sentence>

Your goal is to convert this sentence into first-order predicate logic notation. Follow these guidelines:

1. Use simple English names for predicates.
2. Use $x, $y, $z, etc. as variable names.
3. Create granular predicates. For example, instead of BigHouse($x), use (House($x) ∧ Big($x)).
4. Think carefully about the logical structure of the sentence before providing your output.

Before you give your final answer, take a moment to consider the best way to represent the logical structure of the sentence. You may use <thinking> tags to show your thought process, but this is optional.

Provide your final output enclosed within triple backticks (```). The output should be comprehensible without any surrounding text.

Remember to use granular predicates to break down complex concepts into simpler logical components.

Here's an example to guide you:

Input: "For all students, there exists a course such that if the student is enrolled in the course and the course is difficult, then the student studies hard or seeks help."

Output:
```∀ $x ∃ $y (Student(x) ∧ Course(y) ∧ EnrolledIn(x,y) ∧ Difficult(y)) → ∃ $z ∃ $s ((Studies(z) ∧ Hard(z)  ∧  Does(x,z)) ∨ (Help(s)  ∧ Seeks(x,s)))```

Additionally, here are some examples of previous conversions, please stay consistent with the format and resuse predicates where possible:
{similar}


Now, please convert the given sentence to first-order predicate logic following these instructions.
"""

def convert_to_predicate_logic(line,simiarl): 

    completion = client.chat.completions.create(
        #model="meta-llama/llama-3-70b-instruct",
        #model="openai/gpt-4o",
        model="anthropic/claude-3.5-sonnet",
        temperature=0.5,
        messages=[ {"role": "user","content": format_prompt(line,simiarl), },],
    )
    txt = completion.choices[0].message.content
    return extract_predicate_logic(txt)

def process_file(file_path, skip_lines=0, limit_lines=None):
    res = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines[skip_lines:]):
            if limit_lines is not None and i >= limit_lines:
                break
            simiarl = search_similar_predicates(line.strip())
            pred_logic = convert_to_predicate_logic(line.strip(),simiarl)

            #call shell command plparserexe and capture its output
            metta = os.popen(f"plparserexe {pred_logic}").read().strip()

            print(metta)

            res.append(metta)
            store_embedding_in_qdrant(f"Sentence: {line.strip()}\nPredicate Logic: {pred_logic}")
            print(f"Sentence: {line.strip()}\nPredicate Logic: {metta}")
            with open("data/fol.txt","a") as file:
                file.write(metta + "\n")
                print("last idx: " + str(i))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file and convert sentences to predicate logic.")
    parser.add_argument("file_path", help="Path to the input file")
    parser.add_argument("--skip", type=int, default=0, help="Number of lines to skip at the beginning of the file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to process")
    args = parser.parse_args()

    ensure_predicates_collection()
    process_file(args.file_path, args.skip, args.limit)


