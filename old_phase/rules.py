def rule_based_decision(symptoms: str):
    s = symptoms.lower()

    emergency_keywords = [
        "chest pain",
        "chest tightness",
        "breathlessness",
        "shortness of breath",
        "fainting",
        "severe weakness"
    ]

    for word in emergency_keywords:
        if word in s:
            return {
                "name": "emergency",
                "parameters": {"symptoms": symptoms}
            }

    return None
