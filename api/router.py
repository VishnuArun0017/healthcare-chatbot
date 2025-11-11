"""
Intent router to determine if query should use Graph or Vector RAG
"""
import re


# Patterns that indicate graph-suitable queries
GRAPH_PATTERNS = [
    r'\b(which|what|list|count|how many|any)\b.*\b(avoid|contraindication|should not|shouldn\'t)\b',
    r'\b(which|what|list|count|how many)\b.*\b(provider|hospital|doctor|clinic|specialist)\b',
    r'\b(count|how many)\b.*\b(red flag|symptom|match|warning)\b',
    r'\b(near|in|at)\b.*\b(mumbai|delhi|bangalore|bengaluru|gurgaon|gurugram|chennai|kolkata|pune|city)\b',
    r'\b(avoid|contraindicated)\b.*\b(if i|if you|for)\b',
    r'\b(any)\b.*\b(red flag|warning signs|danger signs)\b',
]

# Known symptom terms that suggest graph query
SYMPTOM_TERMS = {
    "chest pain", "shortness of breath", "headache", "fever", "diarrhea",
    "vomiting", "nausea", "dizziness", "confusion", "seizure",
    "bleeding", "abdominal pain", "cold sweats", "stiff neck",
    "weakness", "fainting", "numbness"
}

CONDITION_TERMS = {"diabetes", "hypertension", "asthma", "heart disease", "kidney disease", "pregnancy"}


def is_graph_intent(text: str) -> bool:
    """
    Determine if query should use graph database
    
    Args:
        text: User query
        
    Returns:
        True if graph query is appropriate
    """
    text_lower = text.lower()
    
    # Check for graph-specific patterns
    for pattern in GRAPH_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    # Check for multiple symptoms (suggests counting/listing or red-flag matching)
    symptom_count = sum(1 for term in SYMPTOM_TERMS if term in text_lower)
    if symptom_count >= 2:
        return True
    
    # Queries combining multiple conditions (e.g., diabetes and hypertension)
    if " and " in text_lower or " with " in text_lower:
        mentioned_conditions = {term for term in CONDITION_TERMS if term in text_lower}
        if len(mentioned_conditions) >= 2:
            return True
    
    # Check for specific keywords
    graph_keywords = [
        "list", "count", "which", "any", "avoid", "contraindication",
        "provider", "hospital", "doctors near", "how many red flags", "is it safe for",
    ]
    if any(keyword in text_lower for keyword in graph_keywords):
        return True
    
    return False


def extract_city(text: str) -> str:
    """
    Extract city name from text
    
    Args:
        text: User query
        
    Returns:
        City name or None
    """
    cities = ["Mumbai", "Delhi", "Bangalore", "Bengaluru", "Gurgaon", "Gurugram", "Chennai", "Kolkata", "Pune", "Hyderabad", "Ahmedabad"]
    text_lower = text.lower()
    
    for city in cities:
        if city.lower() in text_lower:
            # Normalise spelling variants (Bangalore/Bengaluru etc.)
            if city.lower() in {"bengaluru"}:
                return "Bangalore"
            if city.lower() in {"gurugram"}:
                return "Gurgaon"
            return city
    
    return None