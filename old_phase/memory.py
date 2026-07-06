import json
import os

MEMORY_DIR = "patient_memory"

# Ensure directory exists
os.makedirs(MEMORY_DIR, exist_ok=True)

def _memory_file(patient_id):
    return os.path.join(MEMORY_DIR, f"{patient_id}.json")

def get_history(patient_id):
    file_path = _memory_file(patient_id)

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def add_message(patient_id, role, content):
    history = get_history(patient_id)

    history.append({
        "role": role,
        "content": content
    })

    with open(_memory_file(patient_id), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
