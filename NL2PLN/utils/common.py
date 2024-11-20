from typing import Callable, Optional
from openai import OpenAI
import os
import re
from NL2PLN.utils.ragclass import RAG

def parse_lisp_statement(lines: list[str]) -> list[str]:
    """Parse multi-line Lisp-like statements and clean up trailing content after final parenthesis"""
    result = []
    current_statement = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if current_statement is None:
            current_statement = line
        else:
            current_statement = current_statement + ' ' + line
            
        if current_statement.count('(') <= current_statement.count(')'):
            # Find the last closing parenthesis and trim anything after it
            last_paren_idx = current_statement.rindex(')')
            current_statement = current_statement[:last_paren_idx + 1]
            result.append(current_statement)
            current_statement = None
            
    if current_statement is not None:
        result.append(current_statement)
        
    return result

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def extract_logic(response: str) -> dict[str, list[str]] | str | None:
    match = re.search(r'```(.*?)```', response, re.DOTALL)
    if not match:
        return None

    content = match.group(1).strip()

    if content.lower().startswith('performative'):
        return "Performative"
    
    # Split into sections
    from_context = []
    type_definitions = []
    statements = []
    
    # Parse the content looking for sections
    sections = content.split('\n')
    current_section = None
    
    for line in sections:
        line = line.strip()
        if line.lower().startswith('from context:'):
            current_section = 'from_context'
            continue
        elif line.lower().startswith('type definitions:'):
            current_section = 'type_definitions'
            continue
        elif line.lower().startswith('statements:'):
            current_section = 'statements'
            continue
        
        if line:
            if current_section == 'from_context':
                from_context.append(line)
            elif current_section == 'type_definitions':
                type_definitions.append(line)
            elif current_section == 'statements':
                statements.append(line)
    
    if not statements:
        return None
    
    # Parse all sections using the Lisp statement parser
    parsed_context = parse_lisp_statement(from_context)
    parsed_types = parse_lisp_statement(type_definitions)
    parsed_statements = parse_lisp_statement(statements)
        
    return {
        "from_context": parsed_context,
        "type_definitions": parsed_types,
        "statements": parsed_statements
    }

def process_file(file_path: str, process_sentence_func: callable, skip_lines: int = 0, limit_lines: int | None = None) -> None:
    with open(file_path, 'r') as file:
        lines = file.readlines()
        end = len(lines) if limit_lines is None else min(skip_lines + limit_lines, len(lines))
        for i, line in enumerate(lines[skip_lines:end]):
            if not line.strip():
                continue
            if not process_sentence_func(line.strip(), i):
                return

def create_openai_completion(messages: list, model: str = "anthropic/claude-3.5-sonnet", temperature: float = 0.5) -> str:
    headers = {
        "anthropic-beta": "prompt-caching-2024-07-31"
    }
    
    # Flatten messages into the format expected by the API
    api_messages = []
    for msg_group in messages:
        for msg in msg_group:
            if isinstance(msg, dict):
                if "role" in msg:
                    api_messages.append(msg)
                else:
                    api_messages.append({"role": "system", "content": msg.get("text", ""), 
                                       "cache_control": msg.get("cache_control", {})})
    
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=api_messages,
        extra_headers=headers
    )
    if not completion.choices:
        raise Exception("OpenAI API returned no choices")
    return completion.choices[0].message.content
