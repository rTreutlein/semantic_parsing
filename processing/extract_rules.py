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

def load_progress(filename='rules_progress.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get('extracted_rules', []), data.get('current_index', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], 0

def check_rule(sentence): 
    try:
        completion = client.chat.completions.create(
            #model="meta-llama/llama-3.1-8b-instruct",
            model="openai/gpt-4o-mini",
            temperature=0,
            max_tokens=3,  # Set an appropriate max_tokens value
            messages=[
                {
                    "role": "user",
                    "content": f"""Is this sentence a rule, implication, or entailment? '{sentence}' Answer only with Yes or No""",
                },
            ],
        )
        print("-"*100)
        print(sentence)
        print(completion.choices[0].message.content)
        txt = completion.choices[0].message.content
        return sentence, txt
    except Exception as e:
        return sentence, "Error"

def extract_rules(sentences, start_index=0, save_interval=100):
    extracted_rules, current_index = load_progress()
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
            save_progress(extracted_rules, i + save_interval)
    
    # Save final progress
    save_progress(extracted_rules, len(sentences))
    return extracted_rules

if __name__ == "__main__":
    import time

    paragraph = """
    If it rains, the ground gets wet. All mammals are warm-blooded animals. 
    When water reaches 100 degrees Celsius, it boils. This is just a normal sentence. 
    Eating too much sugar leads to weight gain. Lin is sitting at the table.
    """
    
    start_time = time.time()
    rules = extract_rules(paragraph)
    end_time = time.time()
    
