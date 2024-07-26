from openai import OpenAI
from os import getenv
import re
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

def save_progress(extracted_rules, current_index, filename='rules_progress.json'):
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
            temperature=0,
            max_tokens=10,  # Set an appropriate max_tokens value
            messages=[
                {
                    "role": "user",
                    "content": f"""Is this sentence a rule, implication, or entailment? '{sentence}' Answer only with Yes or No""",
                },
            ],
        )
        txt = completion.choices[0].message.content
        print(f"API Response for '{sentence}': {txt}")
        return sentence, txt
    except Exception as e:
        print(f"Error in API call for '{sentence}': {str(e)}", file=sys.stderr)
        return sentence, "Error"

def extract_rules(paragraph, start_index=0, save_interval=10):
    sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
    sentences = [s.strip() for s in sentences if s.strip()]  # Remove empty sentences
    extracted_rules, current_index = load_progress()
    print(f"Current index: {current_index}")
    print(f"Extracted rules: {extracted_rules}")
    print(f"Total sentences: {len(sentences)}")

    print(f"Extracting rules from paragraph: {sentences}")
    
    if start_index > 0:
        current_index = start_index

    with ThreadPoolExecutor(max_workers=save_interval) as executor:
        for i in range(current_index, len(sentences), save_interval):
            batch = sentences[i:i+save_interval]
            futures = [executor.submit(check_rule, sentence) for sentence in batch]
            
            for future in as_completed(futures):
                sentence, out = future.result()
                out = out.strip().replace(".", "")
                if "yes" in out.lower():
                    extracted_rules.append(sentence)
                    print(f"Rule extracted: {sentence}")
                elif "no" in out.lower():
                    print(f"Not a rule: {sentence}")
                elif "error" in out.lower():
                    print(f"Error processing: {sentence}")
                else:
                    print(f"Unexpected output for: {sentence}. Got: {out}")
            
            save_progress(extracted_rules, i + save_interval)
            print(f"Progress saved. Processed {i + save_interval} sentences.")
    
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
