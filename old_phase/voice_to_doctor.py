import requests
from voice_input import transcribe_voice

API_URL = "http://127.0.0.1:8000/doctor/analyze"

patient_id = "amber_01"

text = transcribe_voice()
print("🎙️ Patient said:", text)

payload = {
    "patient_id": patient_id,
    "symptoms": text
}

response = requests.post(API_URL, json=payload)
print("🩺 Doctor Decision:", response.json())
