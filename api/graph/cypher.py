from .client import run_cypher
from typing import List, Dict


def get_red_flags(symptoms: List[str]) -> List[Dict]:
    """
    Query 1: Get conditions that match red flag symptoms
    
    Args:
        symptoms: List of symptom names (will be lowercased)
        
    Returns:
        List of dicts with symptom and associated conditions
    """
    query = """
    MATCH (s:Symptom)-[:IS_RED_FLAG_FOR]->(c:Condition)
    WHERE toLower(s.name) IN $symptoms
    RETURN s.name AS symptom, collect(DISTINCT c.name) AS conditions
    """
    
    # Lowercase all symptoms for case-insensitive matching
    symptoms_lower = [s.lower() for s in symptoms]
    
    try:
        results = run_cypher(query, {"symptoms": symptoms_lower})
        return results
    except Exception as e:
        print(f"Error in get_red_flags: {e}")
        return []


def get_contraindications(user_conditions: List[str]) -> List[Dict]:
    """
    Query 2: Get actions/medications to avoid based on user's conditions
    
    Args:
        user_conditions: List of condition names the user has
        
    Returns:
        List of dicts with actions to avoid and reasons
    """
    query = """
    MATCH (a:Action)-[:AVOID_IN]->(c:Condition)
    WHERE c.name IN $userConditions
    RETURN DISTINCT a.name AS avoid, collect(DISTINCT c.name) AS because
    """
    
    try:
        results = run_cypher(query, {"userConditions": user_conditions})
        return results
    except Exception as e:
        print(f"Error in get_contraindications: {e}")
        return []


def get_safe_actions_for_metabolic_conditions() -> List[Dict]:
    """
    Query 3: Get actions considered safe for diabetes and hypertension profiles
    """
    query = """
    MATCH (a:Action)
    WHERE NOT (a)-[:AVOID_IN]->(:Condition {name:"Diabetes"})
      AND NOT (a)-[:AVOID_IN]->(:Condition {name:"Hypertension"})
    RETURN DISTINCT a.name AS safeAction
    """
    
    try:
        results = run_cypher(query)
        return results
    except Exception as e:
        print(f"Error in get_safe_actions_for_metabolic_conditions: {e}")
        return []


def get_providers_in_city(city: str) -> List[Dict]:
    """
    Query 3: Get healthcare providers in a specific city
    
    Args:
        city: City name
        
    Returns:
        List of dicts with provider info
    """
    query = """
    MATCH (p:Provider)-[:LOCATED_IN]->(l:Location {city: $city})
    OPTIONAL MATCH (p)-[:HAS_MODE]->(s:Service)
    OPTIONAL MATCH (p)-[:HAS_PHONE]->(c:Contact)
    RETURN p.name AS provider, 
           s.name AS mode, 
           c.phone AS phone
    """
    
    try:
        results = run_cypher(query, {"city": city})
        return results
    except Exception as e:
        print(f"Error in get_providers_in_city: {e}")
        return []


def count_red_flags(symptoms: List[str]) -> int:
    """
    Count how many red flag symptoms are matched
    
    Args:
        symptoms: List of symptom names
        
    Returns:
        Count of matched red flags
    """
    results = get_red_flags(symptoms)
    return len(results)


def test_queries():
    """Test all query functions"""
    print("\n" + "=" * 60)
    print("Testing Cypher Queries")
    print("=" * 60)
    
    # Test 1: Red flags
    print("\n1. Testing Red Flag Query:")
    print("   Query: ['chest pain', 'shortness of breath', 'cold sweats']")
    red_flags = get_red_flags(['chest pain', 'shortness of breath', 'cold sweats'])
    for rf in red_flags:
        print(f"   [WARN] {rf['symptom']} -> {', '.join(rf['conditions'])}")
    print(f"   Total red flags matched: {len(red_flags)}")
    
    # Test 2: Contraindications
    print("\n2. Testing Contraindications Query:")
    print("   Query: User has ['Hypertension', 'Diabetes']")
    contras = get_contraindications(['Hypertension', 'Diabetes'])
    for c in contras:
        print(f"   ⛔ Avoid {c['avoid']} (because: {', '.join(c['because'])})")
    
    # Test 3: Providers
    print("\n3. Testing Provider Location Query:")
    print("   Query: Providers in 'Mumbai'")
    providers = get_providers_in_city('Mumbai')
    for p in providers:
        print(f"   🏥 {p['provider']} - {p.get('mode', 'N/A')} - {p.get('phone', 'N/A')}")
    
    print("\n[DONE] Query tests complete!")


if __name__ == "__main__":
    from client import neo4j_client
    
    if neo4j_client.connect():
        try:
            test_queries()
        finally:
            neo4j_client.close()
    else:
        print("[ERROR] Cannot connect to Neo4j for testing")