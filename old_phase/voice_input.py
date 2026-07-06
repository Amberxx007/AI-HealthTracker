import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import os

# Load Whisper model (small = fast, good accuracy)
model = whisper.load_model("small")

SAMPLE_RATE = 16000
RECORD_SECONDS = 6


def record_audio():
    print("🎤 Speak now...")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(temp_file.name, SAMPLE_RATE, audio)
    return temp_file.name


def transcribe_voice():
    wav_file = record_audio()
    result = model.transcribe(wav_file)
    os.remove(wav_file)
    return result["text"]


if __name__ == "__main__":
    text = transcribe_voice()
    print("🧾 Transcribed Text:", text)
