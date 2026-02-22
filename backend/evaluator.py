def evaluate_response(answer: str, chunks_retrieved: int) -> list[str]:
    """
    Evaluates the LLM response and flags any potential issues.
    Returns a list of string flags.
    """
    flags = []
    ans_lower = answer.lower()
    
    # 1. Refusal Check
    refusal_phrases = [
        "i don't have", "i do not have", "not mentioned", "cannot find", 
        "i don't know", "i do not know", "i'm not sure", "i am not sure",
        "does not mention", "doesn't mention", "not provided", "no information"
    ]
    is_refusal = any(phrase in ans_lower for phrase in refusal_phrases)
    if is_refusal:
        flags.append("refusal")
        
    # 2. No Context Check
    if chunks_retrieved == 0 and not is_refusal:
        flags.append("no_context")
        
    # 3. Custom Check: conflicting_sources
    conflict_phrases = ["conflicting", "contradict", "discrepancy", "differ", "unclear"]
    if any(phrase in ans_lower for phrase in conflict_phrases):
        flags.append("conflicting_sources")
        
    return flags
