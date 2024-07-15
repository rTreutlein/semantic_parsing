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

def process_file(file_path):
    res = []
    with open(file_path, 'r') as file:
        for line in file.readlines():
            out = check_sentence(line.strip()).strip().replace(".","")
            if "Yes" in out or "YES" in out:
                res.append(line)
                continue
            if "No" in out or "NO" in out:
                continue
            print(f"No valid output for: {line}Got: {out}")
            continue

    with open("data/llmfiltered.txt","w") as file:
        for sent in res:
            file.write(sent)

if __name__ == "__main__":
    file_path = "data/input.txt"
    process_file(file_path)
