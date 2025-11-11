"""
In-memory fallback for graph queries when Neo4j is not available
"""

# Red flag symptoms and their associated conditions
RED_FLAG_DATA = {
    "chest pain": ["Acute coronary syndrome", "Heart attack", "Pulmonary embolism"],
    "shortness of breath": ["Heart failure", "Pulmonary embolism", "Severe asthma attack"],
    "severe headache": ["Stroke", "Brain hemorrhage", "Meningitis"],
    "one-side weakness": ["Stroke"],
    "difficulty speaking": ["Stroke"],
    "vision changes": ["Stroke"],
    "high fever": ["Sepsis", "Meningitis"],
    "stiff neck": ["Meningitis"],
    "confusion": ["Stroke", "Sepsis", "Diabetic emergency"],
    "seizures": ["Epilepsy", "Brain injury"],
    "heavy bleeding": ["Hemorrhage"],
    "pregnancy bleeding": ["Miscarriage", "Ectopic pregnancy"],
    "severe abdominal pain": ["Appendicitis", "Peritonitis"],
    "blood in stool": ["Gastrointestinal bleeding"],
    "black tarry stool": ["Upper GI bleeding"],
    "persistent vomiting": ["Dehydration", "Bowel obstruction"],
    "suicidal thoughts": ["Mental health crisis"],
    "severe drowsiness": ["Diabetic ketoacidosis", "Hypoglycemia"],
    "bluish lips": ["Hypoxia"],
    "rapid breathing": ["Respiratory distress"],
    "cold sweats": ["Heart attack", "Shock"]
}

# Contraindications by condition
CONTRAINDICATIONS = {
    "Hypertension": ["Ibuprofen", "NSAIDs", "Decongestants", "High sodium foods"],
    "Diabetes": ["Sugary drinks"],
    "Kidney disease": ["Ibuprofen"],
    "Heart disease": ["Ibuprofen", "Decongestants"],
    "Asthma": ["NSAIDs", "Cough suppressants", "Smoking"],
    "Bleeding disorders": ["Aspirin"],
    "Stomach ulcers": ["Aspirin"],
    "Liver disease": ["Alcohol"],
    "Pregnancy": ["Alcohol", "Smoking", "NSAIDs"]
}

# Safe actions by condition
SAFE_ACTIONS = {
    "Hypertension": [
        "Sip oral rehydration solution in small amounts",
        "Practice slow deep-breathing exercises",
        "Rest with head elevated and monitor blood pressure"
    ],
    "Diabetes": [
        "Sip oral rehydration solution in small amounts",
        "Follow the personalised sick-day meal plan from your doctor",
        "Check blood glucose regularly during illness"
    ],
    "Pregnancy": [
        "Stay hydrated with safe warm fluids",
        "Rest on the left side when possible",
        "Contact antenatal care provider for persistent symptoms"
    ]
}

# Healthcare providers by city
PROVIDERS = {
    "Mumbai": [
        {"provider": "Apollo Hospital", "mode": "Emergency", "phone": "1860-500-1066"},
        {"provider": "Lilavati Hospital", "mode": "Emergency", "phone": "+91-22-2640-0000"},
        {"provider": "Kokilaben Hospital", "mode": "Emergency", "phone": "+91-22-4269-6969"}
    ],
    "Delhi": [
        {"provider": "Fortis Hospital", "mode": "Emergency", "phone": "+91-11-4277-6222"},
        {"provider": "Max Hospital", "mode": "Emergency", "phone": "+91-11-2651-5050"},
        {"provider": "AIIMS", "mode": "Emergency", "phone": "+91-11-2658-8500"}
    ],
    "Bangalore": [
        {"provider": "Manipal Hospital", "mode": "Emergency", "phone": "1800-102-5555"},
        {"provider": "Narayana Health", "mode": "Emergency", "phone": "+91-80-7122-2222"},
        {"provider": "Columbia Asia", "mode": "Emergency", "phone": "+91-80-6614-6614"}
    ],
    "Gurgaon": [
        {"provider": "Medanta", "mode": "Emergency", "phone": "+91-124-414-1414"}
    ]
}


def get_red_flags(symptoms):
    """Get red flag conditions for given symptoms"""
    results = []
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        if symptom_lower in RED_FLAG_DATA:
            results.append({
                "symptom": symptom,
                "conditions": RED_FLAG_DATA[symptom_lower]
            })
    return results


def get_contraindications(user_conditions):
    """Get contraindications for user's conditions"""
    results = []
    avoid_set = {}
    
    for condition in user_conditions:
        if condition in CONTRAINDICATIONS:
            for action in CONTRAINDICATIONS[condition]:
                if action not in avoid_set:
                    avoid_set[action] = []
                avoid_set[action].append(condition)
    
    for action, conditions in avoid_set.items():
        results.append({
            "avoid": action,
            "because": conditions
        })
    
    return results


def get_safe_actions(user_conditions):
    """Get safe actions that are acceptable across user's metabolic conditions"""
    if not user_conditions:
        return []
    
    condition_sets = []
    for condition in user_conditions:
        if condition in SAFE_ACTIONS:
            condition_sets.append(set(SAFE_ACTIONS[condition]))
    
    if not condition_sets:
        return []
    
    safe_union = condition_sets[0]
    for s in condition_sets[1:]:
        safe_union = safe_union.intersection(s)
    
    return [{"safeAction": action} for action in sorted(safe_union)]


def get_providers_in_city(city):
    """Get healthcare providers in a city"""
    return PROVIDERS.get(city, [])


def count_red_flags(symptoms):
    """Count matched red flags"""
    return len(get_red_flags(symptoms))