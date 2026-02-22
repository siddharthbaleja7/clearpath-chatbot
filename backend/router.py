def classify_query(query: str) -> str:
    """
    Classify a query as 'simple' or 'complex' using deterministic, rule-based logic.
    """
    words = query.strip().split()
    
    # Rule 1: Query Length
    if len(words) > 15:
        return "complex"
        
    # Rule 2: Complexity Keywords
    # Keywords that imply reasoning, comparison, or troubleshooting
    complex_keywords = [
        "why", "explain", "compare", "difference", "reason",
        "detailed", "how come", "troubleshoot", "issue", "complain",
        "multiple", "vs", "versus"
    ]
    query_lower = query.lower()
    
    import re
    tokens = re.findall(r'\b\w+\b', query_lower)
    if any(kw in tokens for kw in complex_keywords):
        return "complex"

    # For multi-word keywords like "how come"
    if "how come" in query_lower:
        return "complex"

    # Rule 3: Multiple Questions
    if query.count("?") > 1:
        return "complex"

    # Default to simple
    return "simple"

def get_model_for_classification(classification: str) -> str:
    if classification == "complex":
        return "llama-3.3-70b-versatile"
    return "llama-3.1-8b-instant"
