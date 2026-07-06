from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import json

from rules import rule_based_decision
from memory import get_history, add_message
from decision_engine import decide
from voice_api import transcribe_voice

from fastapi import UploadFile, File




LLAMA_URL = "http://localhost:8080/v1/chat/completions"

app = FastAPI(title="AI Doctor v3")

class PatientInput(BaseModel):
    patient_id: str
    symptoms: str


@app.post("/doctor/analyze")
async def analyze_patient(data: PatientInput):

    # 1️⃣ SAFETY RULES (ALWAYS FIRST)
    emergency = rule_based_decision(data.symptoms)
    if emergency:
        reply = (
            "Your symptoms could indicate a medical emergency. "
            "I strongly recommend seeking immediate medical attention or "
            "visiting the nearest hospital right now."
        )
        add_message(data.patient_id, "user", data.symptoms)
        add_message(data.patient_id, "assistant", reply)
        return {
            "decision": emergency,
            "reply": reply
        }

    # 2️⃣ MEMORY
    history = get_history(data.patient_id)

    system_prompt = """
You are a compassionate human doctor talking directly to the patient.

Guidelines:
- Speak naturally like a real doctor in a clinic
- Do NOT mention AI, models, analysis, or systems
- Explain what the problem could be in simple words
- Explain why it may be happening
- Give practical precautions
- Suggest safe home remedies if appropriate
- Gently advise seeing a doctor if symptoms worsen
- Do NOT ask too many questions at once
- Write in short friendly paragraphs
- No bullet points, no numbers, no formatting
"""


    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": data.symptoms})

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "messages": messages,
        "temperature": 0.35
    }

    response = requests.post(LLAMA_URL, json=payload).json()
    reply = response["choices"][0]["message"]["content"].strip()

    add_message(data.patient_id, "user", data.symptoms)
    add_message(data.patient_id, "assistant", reply)

    return {
        "decision": {
            "name": "medical_guidance"
    },
    "reply": reply
}



@app.get("/api/status")
def status():
    return {"status": "AI Doctor v3 running"}


app.mount("/ui", StaticFiles(directory="static", html=True), name="ui")

from fastapi import UploadFile, File


@app.post("/doctor/voice")
async def voice_input(patient_id: str, audio: UploadFile = File(...)):

    audio_bytes = await audio.read()
    voice = transcribe_voice(audio_bytes)

    response = await analyze_patient(PatientInput(
        patient_id=patient_id,
        symptoms=voice["english_text"]
    ))

    reply_en = response["reply"]

    if voice["language"] != "en":
        reply_local = Translator().translate(
            reply_en, dest=voice["language"]
        ).text
    else:
        reply_local = reply_en

    audio_path = f"static/reply_{patient_id}.mp3"
    gTTS(reply_local, lang=voice["language"]).save(audio_path)

    return {
        "user_spoken": voice["original_text"],
        "reply_text": reply_local,
        "reply_audio": f"/{audio_path}"
    }
