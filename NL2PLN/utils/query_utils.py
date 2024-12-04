from NL2PLN.utils.common import create_openai_completion, extract_logic

def convert_to_english(pln_text, similar_examples, previous_sentences=None):
    """
    Convert PLN expressions to natural language English.
    
    Args:
        pln_text: The PLN expression to convert
        similar_examples: List of similar examples
        previous_sentences: List of previous context sentences
    
    Returns:
        str: The English translation of the PLN expression
    """
    from NL2PLN.utils.prompts import pln2nl
    system_msg, user_msg = pln2nl(pln_text, similar_examples, previous_sentences or [])
    response = create_openai_completion(system_msg, user_msg)
    
    # Extract the English text from between triple backticks
    import re
    match = re.search(r'```(.+?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()

def convert_logic_simple(input_text, prompt_func, similar_examples, previous_sentences=None):
    """
    Simplified version of convert_logic that doesn't include human validation.
    """
    system_msg, user_msg = prompt_func(input_text, similar_examples, previous_sentences or [])
    txt = create_openai_completion(system_msg, user_msg)
    
    logic_data = extract_logic(txt)
    if logic_data is None:
        raise RuntimeError("No output from LLM")
    
    return logic_data
