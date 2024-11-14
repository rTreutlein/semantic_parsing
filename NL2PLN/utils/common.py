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
    if not match:
        return None
        
    content = match.group(1).strip()
    
    # Split into preconditions and statement sections
    preconditions = []
    statement = None
    
    # Parse the content looking for Preconditions: and Statement: sections
    sections = content.split('\n')
    current_section = None
    
    for line in sections:
        line = line.strip()
        if line.lower().startswith('preconditions:'):
            current_section = 'preconditions'
            continue
        elif line.lower().startswith('statement:'):
            current_section = 'statement'
            continue
        
        if line and current_section == 'preconditions':
            preconditions.append(line)
        elif line and current_section == 'statement':
            statement = line
    
    if statement is None:
        return None
        
    return {
        "preconditions": preconditions,
        "statement": statement
    }

def process_file(file_path, process_sentence_func, skip_lines=0, limit_lines=None):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        end = len(lines) if limit_lines is None else min(skip_lines + limit_lines, len(lines))
        for i, line in enumerate(lines[skip_lines:end]):
            process_sentence_func(line.strip(), i)

def create_openai_completion(prompt, model="anthropic/claude-3.5-sonnet", temperature=0.5):
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    if not completion.choices:
        print(completion)
        raise Exception("OpenAI API returned no choices")
    return completion.choices[0].message.content
