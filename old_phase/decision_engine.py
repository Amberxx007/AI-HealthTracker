from rules import rule_based_decision
import json
import requests

LLAMA_URL = "http://localhost:8080/v1/chat/completions"

def decide(symptoms: str):
    # 1️⃣ HARD RULES FIRST
    rule = rule_based_decision(symptoms)
    if rule:
        return rule["name"]

    # 2️⃣ AI DECISION (STRICT)
    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a medical triage engine.\n"
                    "Return ONLY one word:\n"
                    "emergency OR assess_symptoms OR home_care"
                )
            },
            {
                "role": "user",
                "content": symptoms
            }
        ],
        "temperature": 0
    }

    r = requests.post(LLAMA_URL, json=payload).json()
    decision = r["choices"][0]["message"]["content"].strip().lower()

    if decision not in ["emergency", "assess_symptoms", "home_care"]:
        return "assess_symptoms"

    return decision
