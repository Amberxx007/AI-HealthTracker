import subprocess

def transcribe_audio(audio_path):
    cmd = [
        "whisper.cpp/build/bin/Release/whisper-cli.exe",
        "-m", "whisper.cpp/models/ggml-base.en.bin",
        "-f", audio_path
    ]
    output = subprocess.check_output(cmd, text=True)
    return output.strip()
