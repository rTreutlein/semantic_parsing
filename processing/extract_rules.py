from openai import OpenAI
from os import getenv
import re
import json
import time
import sys

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

def save_progress(extracted_rules, current_index, filename='progress.json'):
    with open(filename, 'w') as f:
        json.dump({'extracted_rules': extracted_rules, 'current_index': current_index}, f)

def load_progress(filename='progress.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get('extracted_rules', []), data.get('current_index', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], 0

def check_rule(sentence): 
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            temperature = 0,
            messages=[
                {
                    "role": "user",
                    "content": f"""Is this sentence a rule, implication, or entailment? '{sentence}' Answer only with Yes or No""",
                },
            ],
        )
        txt = completion.choices[0].message.content
        print(f"API Response: {txt}")
        return txt
    except Exception as e:
        print(f"Error in API call: {str(e)}", file=sys.stderr)
        return "Error"

def extract_rules(paragraph, start_index=0, save_interval=10):
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
    extracted_rules, current_index = load_progress()
    print(f"Current index: {current_index}")
    print(f"Extracted rules: {extracted_rules}")

    print(f"Extracting rules from paragraph: {sentences}")
    
    if start_index > 0:
        current_index = start_index
    
    for i, sentence in enumerate(sentences[current_index:], start=current_index):
        print(f"Processing sentence {i + 1}: {sentence}")
        out = check_rule(sentence.strip()).strip().replace(".", "")
        if "yes" in out.lower():
            extracted_rules.append(sentence)
            print(f"Rule extracted: {sentence}")
        elif "no" in out.lower():
            print(f"Not a rule: {sentence}")
        elif "error" in out.lower():
            print(f"Error processing: {sentence}")
        else:
            print(f"Unexpected output for: {sentence}. Got: {out}")
        
        if (i + 1) % save_interval == 0:
            save_progress(extracted_rules, i + 1)
            print(f"Progress saved. Processed {i + 1} sentences.")
        
        time.sleep(1)  # Add a 1-second delay between API calls
    
    # Save final progress
    save_progress(extracted_rules, len(sentences))
    return extracted_rules

if __name__ == "__main__":
    paragraph = """
    If it rains, the ground gets wet. All mammals are warm-blooded animals. 
    When water reaches 100 degrees Celsius, it boils. This is just a normal sentence. 
    Eating too much sugar leads to weight gain. Lin is sitting at the table.
    """
    rules = extract_rules(paragraph)
    print("Extracted rules:")
    for rule in rules:
        print(rule)
