from openai import OpenAI
from os import getenv
import re

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

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

def filter_sentences(sentences):
    filtered_sentences = []
    for sentence in sentences:
        out = check_sentence(sentence.strip()).strip().replace(".", "")
        if "Yes" in out or "YES" in out:
            filtered_sentences.append(sentence)
        elif "No" in out or "NO" in out:
            continue
        else:
            print(f"No valid output for: {sentence}Got: {out}")
    return filtered_sentences

#if __name__ == "__main__":
    #sentences = [
    #    "This is a complete sentence.",
    #    "Not a complete",
    #    "Another full sentence here.",
    #    "Incomplete phrase"
    #]
    #filtered = filter_sentences(sentences)
    #print("Filtered sentences:")
    #for sentence in filtered:
    #    print(sentence)
