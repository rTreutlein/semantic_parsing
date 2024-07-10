from openai import openai
import os
import re
from rag import store_embedding_in_qdrant, ensure_predicates_collection, search_similar_predicates

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

def extract_predicate_logic(response):
    match = re.search(r'```(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def extract_predicates(pred_logic):
    match = re.search(r'\(([A-Z][a-zA-Z]*)', pred_logic, re.DOTALL)
    predicates = []
    while match:
        predicates.append(match.group(1))
        pred_logic = pred_logic[match.end():]
        match = re.search(r'\(([A-Z][a-zA-Z]*)', pred_logic, re.DOTALL)
    return predicates

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

def get_max_elem(expressions):
    cnts = dict()
    for exp in expressions:
        cnts.setdefault(exp,0)
        cnts[exp] += 1
    max = 0
    max_elem = "Default Value"
    for key, val in cnts.items():
        if max < val:
            max = val
            max_elem = key
    return max,max_elem


def process_file(file_path, skip_lines=0, limit_lines=None):
    res = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines[skip_lines:]):
            if limit_lines is not None and i >= limit_lines:
                break
            simiarl = search_similar_predicates(line.strip())
            pred_logic = convert_to_predicate_logic(line.strip(),simiarl)

            #call shell command plparserexe
            metta = os.system(f"plparserexe {pred_logic}")

            res.append(metta)
            store_embedding_in_qdrant(f"Sentence: {line.strip()}\nPredicate Logic: {pred_logic}")
            print(f"Sentence: {line.strip()}\nPredicate Logic: {max_elem}\nPreicates: {preds}")
            with open("data/fol.txt","a") as file:
                file.write(max_elem + "\n")
                print("last idx: " + str(i))

if __name__ == "__main__":
    #file_path = "data/test.txt"
    file_path = "data/sorted.txt"
    skip_lines = 7  # Example value, adjust as needed
    limit_lines = 100  # Example value, adjust as needed
    ensure_predicates_collection()
    process_file(file_path, skip_lines, limit_lines)


