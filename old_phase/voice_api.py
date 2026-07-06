import whisper, tempfile, os
from langdetect import detect

model = whisper.load_model("base")

def transcribe_voice(audio_bytes: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        path = f.name

    result = model.transcribe(path)
    text = result["text"].strip()

    lang = detect(text)

    if lang != "en":
        english = GoogleTranslator(source=lang, target="en").translate(text)
    else:
        english = text

    os.remove(path)

    return {
        "original_text": text,
        "english_text": english,
        "language": lang,
        "error": None
    }
    