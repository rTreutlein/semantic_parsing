from typing import Callable, Optional
import anthropic
import os
import re
import time
import tempfile
import shutil
from NL2PLN.utils.ragclass import RAG

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

def parse_lisp_statement(lines: list[str]) -> list[str]:
    """Parse multi-line Lisp-like statements and clean up trailing content after final parenthesis"""
    result = []
    current_statement = None
    
    for line in lines:
        line = line.strip()
        if not line or not line.startswith('('):
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
    questions = []
    
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
        elif line.lower().startswith('questions:'):
            current_section = 'questions'
            continue
        
        if line:
            if current_section == 'from_context':
                from_context.append(line)
            elif current_section == 'type_definitions':
                type_definitions.append(line)
            elif current_section == 'statements':
                statements.append(line)
            elif current_section == 'questions':
                questions.append(line)
    
    if not statements and not questions:
        return None
    
    # Parse all sections using the Lisp statement parser
    parsed_context = parse_lisp_statement(from_context)
    parsed_types = parse_lisp_statement(type_definitions)
    parsed_statements = parse_lisp_statement(statements)
    parsed_questions = parse_lisp_statement(questions)
        
    return {
        "from_context": parsed_context,
        "type_definitions": parsed_types,
        "statements": parsed_statements,
        "questions": parsed_questions
    }

def process_file(file_path: str, process_sentence_func: callable, skip_lines: int = 0, limit_lines: int | None = None) -> None:
    # Create a temporary file
    temp_fd, temp_path = tempfile.mkstemp(text=True)
    os.close(temp_fd)
    
    try:
        # Copy original content to temp file
        shutil.copyfile(file_path, temp_path)
        
        with open(temp_path, 'r') as file:
            lines = file.readlines()
            end = len(lines) if limit_lines is None else min(skip_lines + limit_lines, len(lines))
            
            for i, line in enumerate(lines[skip_lines:end]):
                if not line.strip():
                    continue
                    
                if not process_sentence_func(line.strip(), i):
                    break
                
                # Remove processed line from temp file
                with open(temp_path, 'w') as temp_file:
                    temp_file.writelines(lines[i+skip_lines+1:])
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def create_openai_completion(system_msg, user_msg, model: str = "claude-3-5-sonnet-20241022", max_retries: int = 3) -> str:
    # Convert message format for Anthropic
    retry_count = 0
    base_delay = 1  # Start with 1 second delay

    while True:
        try:
            response = client.beta.prompt_caching.messages.create(
                model=model,
                max_tokens=1024,
                system=system_msg,
                messages=user_msg,
            )
            return response.content[0].text

        except anthropic.APIStatusError as e:
            if e.status_code == 529 and retry_count < max_retries:  # Overloaded error
                retry_count += 1
                delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                print(f"API overloaded. Retrying in {delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(delay)
                continue
            raise  # Re-raise the exception if we're out of retries or it's a different error
