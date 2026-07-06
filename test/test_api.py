import requests

url = "http://127.0.0.1:8000/doctor/analyze"
data = {
    "patient_id": "amber01",
    "symptoms": "headache for 2 days"
}

r = requests.post(url, json=data)
print(r.json())
