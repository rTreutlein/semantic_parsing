from NL2PLN.utils.common import create_openai_completion, extract_logic

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
