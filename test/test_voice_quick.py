"""
Quick test for faster-whisper (STT) and edge-tts (TTS)
Run: python test/test_voice_quick.py
"""
import asyncio
import os
import time

# ─── Test 1: edge-tts (Text-to-Speech) ───
async def test_tts():
    import edge_tts

    os.makedirs("test/tts_output", exist_ok=True)

    tests = [
        ("en", "en-IN-NeerjaNeural",   "Hello, I am your AI Doctor. How can I help you today?", "test_english.mp3"),
        ("hi", "hi-IN-SwaraNeural",    "नमस्ते, मैं आपकी AI डॉक्टर हूँ। आज मैं आपकी कैसे मदद कर सकती हूँ?", "test_hindi.mp3"),
        ("pa", "hi-IN-SwaraNeural",   "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ ਤੁਹਾਡਾ AI ਡਾਕਟਰ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?", "test_punjabi.mp3"),
    ]

    for lang, voice, text, filename in tests:
        filepath = f"test/tts_output/{filename}"
        print(f"\n🔊 TTS [{lang}] → {voice}")
        print(f"   Text: {text}")

        t0 = time.time()
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
        elapsed = time.time() - t0

        size_kb = os.path.getsize(filepath) / 1024
        print(f"   ✅ Saved: {filepath} ({size_kb:.0f} KB, {elapsed:.1f}s)")
        print(f"   ▶  Play it: start {filepath}")

    print("\n" + "="*60)
    print("🎧 Open test/tts_output/ folder and play the MP3 files!")
    print("="*60)


# ─── Test 2: faster-whisper (Speech-to-Text) ───
def test_stt():
    from faster_whisper import WhisperModel
    import glob

    # Find any existing audio file to test with
    audio_files = glob.glob("test/tts_output/*.mp3") + glob.glob("static/audio/*.wav") + glob.glob("static/audio/*.mp3")

    if not audio_files:
        print("\n⚠️  No audio files found to test STT.")
        print("   Run TTS test first, then re-run this script.")
        return

    print(f"\n🎙️  Loading faster-whisper model (medium)...")
    t0 = time.time()
    try:
        model = WhisperModel("medium", device="cuda", compute_type="float16")
        print(f"   Loaded on CUDA ({time.time()-t0:.1f}s)")
    except Exception:
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        print(f"   Loaded on CPU ({time.time()-t0:.1f}s)")

    # Test transcription on the TTS output files (round-trip test!)
    for audio_file in audio_files[:3]:
        print(f"\n🎙️  STT: {os.path.basename(audio_file)}")
        t0 = time.time()
        segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True)

        text = ""
        for seg in segments:
            text += seg.text

        elapsed = time.time() - t0
        print(f"   Language: {info.language} (confidence: {info.language_probability:.0%})")
        print(f"   Text: {text.strip()}")
        print(f"   ⏱️  Time: {elapsed:.1f}s")


# ─── Main ───
async def main():
    print("="*60)
    print("  AI Doctor v3 — Voice Model Quick Test")
    print("="*60)

    print("\n📢 TEST 1: Text-to-Speech (edge-tts)")
    print("-"*40)
    await test_tts()

    print("\n\n📢 TEST 2: Speech-to-Text (faster-whisper)")
    print("-"*40)
    test_stt()

    print("\n\n✅ All tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
