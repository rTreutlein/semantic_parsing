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
