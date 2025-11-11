"""
Safety detection module for identifying red flag symptoms
"""

# Red flag keywords in English and Hindi (transliterated)
RED_FLAGS = {
    # Cardiac/Chest
    "chest pain", "chest pressure", "crushing chest", "seene mein dard",
    "cold sweats", "thandi pasina",
    "tightness in chest", "pressure in chest",
    
    # Respiratory
    "shortness of breath", "can't breathe", "difficulty breathing",
    "saans nahi aa rahi", "saans lene mein takleef",
    "saans ruk raha", "breathlessness", "gasping for air",
    "bluish lips", "blue face", "honth neele",
    
    # Neurological
    "severe headache", "worst headache", "sudden headache", "thunderclap headache",
    "one-side weakness", "weakness one side", "ek taraf kamzori", "one sided weakness",
    "body numb one side", "haath pair sunn",
    "difficulty speaking", "slurred speech", "bolne mein dikkat",
    "vision changes", "sudden vision loss", "dekhne mein dikkat", "double vision",
    "confusion", "disoriented", "behoshi",
    "seizure", "convulsion", "daura",
    "stiff neck", "gardan akad",
    
    # Bleeding/Trauma
    "heavy bleeding", "severe bleeding", "khoon beh raha", "uncontrolled bleeding",
    "blood in stool", "black stool", "pakhana mein khoon",
    "blood in vomit", "ulti mein khoon",
    "pregnancy bleeding", "garbhavastha mein khoon", "pregnancy heavy bleeding",
    "pregnancy severe pain", "garbhavastha mein tez dard",
    
    # Abdominal
    "severe abdominal pain", "severe stomach pain", "pet mein bahut dard", "pet mein tez dard",
    
    # Fever/Infection
    "high fever child", "infant fever", "bacche ko tez bukhar", "baby fever high",
    "fever not reducing", "uncontrolled fever",
    
    # Mental Health
    "suicidal thoughts", "want to die", "khudkushi",
    "self harm", "hurt myself", "end my life", "khud ko nuksan",
    
    # Diabetic Emergency
    "very high sugar", "sugar 300", "sugar 400",
    "fruity breath", "rapid breathing with diabetes",
    
    # Dehydration / Shock
    "severe dehydration", "pani ki bahut kami", "bahut zyada pani ki kami",
    "no urine", "passing very little urine",
}


def detect_red_flags(text: str, lang: str = "en") -> dict:
    """
    Detect red flag symptoms in user text
    
    Args:
        text: User's message
        lang: Language code (en/hi)
        
    Returns:
        Dict with red_flag boolean and matched list
    """
    text_lower = text.lower()
    matched = []
    
    for flag in RED_FLAGS:
        if flag in text_lower:
            matched.append(flag)
    
    matched_unique = sorted(set(matched))
    
    return {
        "red_flag": len(matched_unique) > 0,
        "matched": matched_unique
    }


def extract_symptoms(text: str) -> list:
    """
    Extract symptom keywords from text for graph queries
    
    Args:
        text: User's message
        
    Returns:
        List of symptom strings
    """
    # Common symptom keywords
    SYMPTOMS = {
        "chest pain", "shortness of breath", "fever", "cough", "sore throat",
        "headache", "diarrhea", "vomiting", "nausea", "dizziness",
        "fatigue", "body ache", "cold sweats", "confusion", "seizures",
        "heavy bleeding", "severe abdominal pain", "stiff neck",
        "one-side weakness", "difficulty speaking", "vision changes",
        "bluish lips", "rapid breathing", "high fever", "dehydration"
    }
    
    text_lower = text.lower()
    found = []
    
    for symptom in SYMPTOMS:
        if symptom in text_lower:
            found.append(symptom)
    
    return found