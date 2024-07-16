from openai import OpenAI
from os import getenv
import re
import json

# Rename this file to filter_sentences_llm.py

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

def save_progress(filtered_sentences, current_index, filename='progress.json'):
    with open(filename, 'w') as f:
        json.dump({'filtered_sentences': filtered_sentences, 'current_index': current_index}, f)

def load_progress(filename='progress.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['filtered_sentences'], data['current_index']
    except FileNotFoundError:
        return [], 0

def check_sentence(line): 
    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        #model="meta-llama/llama-3-70b-instruct",
        #model="openai/gpt-4o",
        temperature = 0,
        messages=[
            {
                "role": "user",
                "content": f"""Is this a complete sentence: '{line}' Answer only with Yes or No""",
            },
         
        ],
    )
    txt = completion.choices[0].message.content
    return txt

def filter_sentences(sentences, start_index=0, save_interval=10):
    filtered_sentences, current_index = load_progress()
    
    if start_index > 0:
        current_index = start_index
    
    for i, sentence in enumerate(sentences[current_index:], start=current_index):
        out = check_sentence(sentence.strip()).strip().replace(".", "")
        if "Yes" in out or "YES" in out:
            filtered_sentences.append(sentence)
        elif "No" in out or "NO" in out:
            continue
        else:
            print(f"No valid output for: {sentence}Got: {out}")
        
        if (i + 1) % save_interval == 0:
            save_progress(filtered_sentences, i + 1)
            print(f"Progress saved. Processed {i + 1} sentences.")
    
    # Save final progress
    save_progress(filtered_sentences, len(sentences))
    return filtered_sentences

if __name__ == "__main__":
    sentences = [
        "This is a complete sentence.",
        "Not a complete",
        "Another full sentence here.",
        "Incomplete phrase"
    ]
    filtered = filter_sentences(sentences)
    print("Filtered sentences:")
    for sentence in filtered:
        print(sentence)
