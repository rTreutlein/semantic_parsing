from NL2PLN.utils.common import create_openai_completion, extract_logic

def is_question(text: str) -> bool:
    """
    Simple heuristic to determine if text is a question.
    This is a placeholder - should be replaced with more sophisticated logic.
    """
    text = text.strip().lower()
    question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose']
    return (
        any(text.startswith(word) for word in question_words) or
        text.endswith('?')
    )

def convert_logic_simple(input_text, prompt_func, similar_examples, previous_sentences=None):
    """
    Simplified version of convert_logic that doesn't include human validation.
    """
    system_msg, user_msg = prompt_func(input_text, similar_examples, previous_sentences or [])
    txt = create_openai_completion(system_msg, user_msg)
    print("--------------------------------------------------------------------------------")
    print("LLM output:")
    print(txt)
    
    logic_data = extract_logic(txt)
    if logic_data is None:
        raise RuntimeError("No output from LLM")
    
    return logic_data
