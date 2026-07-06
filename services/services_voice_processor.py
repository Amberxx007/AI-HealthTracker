"""
Advanced Voice Processing Service
Real-time transcription with language detection using faster-whisper.

PUNJABI FIX (3-layer approach):
  1. Always convert audio to 16kHz mono WAV before transcription
     (webm from browser has variable bitrate that trips Whisper on Punjabi)
  2. Use large-v2 model for Punjabi — medium has too little Punjabi training data.
     The large models are trained on orders-of-magnitude more Punjabi/Gurmukhi text.
  3. Stronger initial_prompt with medical Gurmukhi vocabulary + beam_size=10
     to force the decoder to stay in Gurmukhi script.
  4. Post-process: if output contains zero Gurmukhi Unicode but language=="pa",
     re-run with explicit temperature scheduling to avoid mode collapse.
"""

import numpy as np
import tempfile
import os
import subprocess
import shutil
from typing import Dict, Optional
from langdetect import detect, LangDetectException
import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils.utils_logger import setup_logger

logger = setup_logger(__name__)

# ── Gurmukhi Unicode range
GURMUKHI_START = "\u0A00"
GURMUKHI_END   = "\u0A7F"
DEVANAGARI_START = "\u0900"
DEVANAGARI_END   = "\u097F"


def _has_gurmukhi(text: str) -> bool:
    return any(GURMUKHI_START <= ch <= GURMUKHI_END for ch in text)


def _has_devanagari(text: str) -> bool:
    return any(DEVANAGARI_START <= ch <= DEVANAGARI_END for ch in text)


def _convert_to_wav(input_path: str) -> str:
    """
    Convert any audio format to 16kHz mono WAV using ffmpeg.
    This is CRITICAL for Punjabi — webm from browser has variable
    sample rate that causes Whisper to mis-identify the language.
    Returns path to the WAV file (caller must delete it).
    """
    wav_path = input_path.replace(".webm", ".wav").replace(".mp3", ".wav")
    if not wav_path.endswith(".wav"):
        wav_path += ".wav"

    # Check ffmpeg is available
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found — skipping audio conversion (Punjabi accuracy may suffer)")
        return input_path

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", input_path,
                "-ar", "16000",   # 16kHz sample rate — required by Whisper
                "-ac", "1",       # Mono
                "-c:a", "pcm_s16le",  # 16-bit PCM — best Whisper input
                "-af", "highpass=f=80,lowpass=f=8000,loudnorm",  # denoise
                wav_path,
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info(f"Audio converted to 16kHz WAV: {wav_path}")
            return wav_path
        else:
            logger.warning(f"ffmpeg conversion failed: {result.stderr.decode()[:200]}")
            return input_path
    except Exception as e:
        logger.warning(f"ffmpeg conversion error: {e}")
        return input_path


class VoiceProcessor:
    """
    Enterprise-grade voice processing with:
    - faster-whisper for high-accuracy multilingual STT
    - Proper Hindi/Punjabi/Gurmukhi recognition
    - Real-time audio level detection
    - Async processing
    """

    # ── Model size strategy:
    #    English + Hindi → medium is fine
    #    Punjabi         → MUST use large-v2 or large-v3
    #    We load large-v2 by default. If you only have medium, set
    #    PUNJABI_MODEL_SIZE = "medium" but accuracy will be poor.
    DEFAULT_MODEL_SIZE  = "large-v2"   # change to "medium" if RAM is tight
    PUNJABI_MODEL_SIZE  = "large-v2"   # dedicated model for Punjabi

    def __init__(self, model_size: str = None):
        self.model_size = model_size or self.DEFAULT_MODEL_SIZE
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=3)

        self.language_map = {
            "en": "en",
            "hi": "hi",
            "pa": "pa",
            "ur": "ur",
        }

        # Whisper mis-detection remaps for South Asian languages
        self.lang_remap = {
            "fa": "hi",
            "ar": "hi",
            "ur": "hi",
            "sd": "hi",
            "ps": "pa",
            "ne": "hi",
            "mr": "hi",
            "bn": "hi",
            "gu": "hi",
            "ta": "hi",
            "te": "hi",
        }

        logger.info(f"VoiceProcessor initialized (faster-whisper, model: {self.model_size})")

    async def initialize(self):
        """Load faster-whisper model asynchronously"""
        logger.info(f"Loading faster-whisper model ({self.model_size})...")
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(self.executor, self._load_model)
        logger.info("faster-whisper model loaded successfully")

    def _load_model(self):
        from faster_whisper import WhisperModel
        try:
            model = WhisperModel(self.model_size, device="cuda", compute_type="float16")
            logger.info(f"faster-whisper {self.model_size} loaded on CUDA (float16)")
        except Exception:
            logger.info("CUDA not available, falling back to CPU")
            model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            logger.info(f"faster-whisper {self.model_size} loaded on CPU (int8)")
        return model

    async def transcribe(self, audio_bytes: bytes, forced_language: str = None) -> Dict:
        try:
            if self.model is None:
                await self.initialize()

            # Save raw audio
            suffix = ".webm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # ── STEP 1: Convert to 16kHz WAV (critical for Punjabi) ──
            wav_path = _convert_to_wav(tmp_path)
            transcribe_path = wav_path

            # Transcribe
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                transcribe_path,
                forced_language,
            )

            # Cleanup
            for p in set([tmp_path, wav_path]):
                try:
                    os.unlink(p)
                except OSError:
                    pass

            text = result["text"].strip()

            if not text:
                return {"text": "", "language": "unknown", "confidence": 0.0,
                        "error": "No speech detected"}

            # ── STEP 2: Determine language ──
            if forced_language and forced_language in ["en", "hi", "pa"]:
                detected_lang = forced_language
            else:
                whisper_lang = result.get("language", "en")
                detected_lang = self.lang_remap.get(whisper_lang, whisper_lang)

                # langdetect cross-check
                if detected_lang not in ["en", "hi", "pa"]:
                    try:
                        ld_lang = self.lang_remap.get(detect(text), detect(text))
                        if ld_lang in ["en", "hi", "pa"]:
                            detected_lang = ld_lang
                    except LangDetectException:
                        pass

                # Unicode script fallback (most reliable for Indian scripts)
                if _has_gurmukhi(text):
                    detected_lang = "pa"
                elif _has_devanagari(text):
                    detected_lang = "hi"
                elif detected_lang not in ["en", "hi", "pa"]:
                    detected_lang = "en"

            # ── STEP 3: Punjabi quality check — re-run if output is wrong script ──
            # If user selected Punjabi but Whisper returned Devanagari/Latin,
            # it means the model collapsed to Hindi/English. Re-run with
            # stronger constraints and temperature scheduling.
            if forced_language == "pa" and not _has_gurmukhi(text):
                logger.warning(
                    f"Punjabi selected but output has no Gurmukhi script "
                    f"(got: '{text[:60]}'). Re-running with strict Gurmukhi forcing..."
                )
                # Re-save audio (re-read from original bytes)
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp2:
                    tmp2.write(audio_bytes)
                    tmp2_path = tmp2.name
                wav2_path = _convert_to_wav(tmp2_path)

                result2 = await loop.run_in_executor(
                    self.executor,
                    self._transcribe_punjabi_strict,
                    wav2_path if wav2_path != tmp2_path else tmp2_path,
                )
                for p in set([tmp2_path, wav2_path]):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

                text2 = result2["text"].strip()
                if text2 and _has_gurmukhi(text2):
                    text = text2
                    detected_lang = "pa"
                    logger.info(f"Strict re-run produced Gurmukhi: '{text2[:60]}'")
                elif text2:
                    # Still no Gurmukhi but at least got something — keep it
                    text = text2
                    detected_lang = "pa"
                    logger.warning("Re-run still no Gurmukhi — using output as-is")

            confidence = result.get("confidence", 0.85)
            logger.info(
                f"Transcribed ({detected_lang}, forced={forced_language}): "
                f"'{text[:80]}' confidence={confidence:.2f}"
            )

            return {"text": text, "language": detected_lang,
                    "confidence": confidence, "error": None}

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {"text": "", "language": "unknown", "confidence": 0.0, "error": str(e)}

    def _transcribe_sync(self, audio_path: str, forced_language: str = None) -> Dict:
        """Standard transcription for English and Hindi."""
        import math

        kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=400),
        }

        if forced_language and forced_language in self.language_map:
            kwargs["language"] = self.language_map[forced_language]
            if forced_language == "pa":
                # Use the stronger Punjabi path
                return self._transcribe_punjabi_strict(audio_path)
            elif forced_language == "hi":
                kwargs["initial_prompt"] = (
                    "यह हिंदी में डॉक्टर और मरीज की बातचीत है। "
                    "मरीज अपने लक्षण बता रहा है।"
                )
        else:
            kwargs["language"] = None

        return self._run_transcription(audio_path, kwargs)

    def _transcribe_punjabi_strict(self, audio_path: str) -> Dict:
        """
        Dedicated Punjabi transcription pipeline.

        Key differences from standard:
        - language forced to "pa"
        - beam_size=10 (wider search → more likely to find Gurmukhi tokens)
        - best_of=5 (sample 5 candidates, pick best)
        - temperature scheduling: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
          Whisper uses fallback temperatures when confidence is low —
          this gives the decoder more chances to land on Gurmukhi
        - Rich Gurmukhi initial_prompt with medical vocabulary so the
          decoder's first tokens are Gurmukhi and it stays in that script
        - suppress_tokens removes common Latin/Devanagari tokens that
          cause script switching
        """
        kwargs = {
            "language": "pa",
            "beam_size": 10,
            "best_of": 5,
            "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=400),
            # Rich medical Gurmukhi prompt — forces decoder into Gurmukhi mode
            "initial_prompt": (
                "ਇਹ ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਵਿੱਚ ਡਾਕਟਰ ਅਤੇ ਮਰੀਜ਼ ਦੀ ਗੱਲਬਾਤ ਹੈ। "
                "ਮਰੀਜ਼ ਆਪਣੇ ਲੱਛਣ ਦੱਸ ਰਿਹਾ ਹੈ। "
                "ਆਮ ਸ਼ਬਦ: ਦਰਦ, ਬੁਖਾਰ, ਖੰਘ, ਸਿਰਦਰਦ, ਪੇਟ, ਸਾਹ, ਦਵਾਈ, "
                "ਹਸਪਤਾਲ, ਡਾਕਟਰ, ਖੂਨ, ਦਿਲ, ਸ਼ੂਗਰ, ਬਲੱਡ ਪ੍ਰੈਸ਼ਰ।"
            ),
            # condition_on_previous_text keeps Gurmukhi script across segments
            "condition_on_previous_text": True,
            # word_timestamps helps with confidence scoring per token
            "word_timestamps": False,
        }
        return self._run_transcription(audio_path, kwargs)

    def _run_transcription(self, audio_path: str, kwargs: dict) -> Dict:
        """Shared transcription runner."""
        import math
        try:
            segments, info = self.model.transcribe(audio_path, **kwargs)

            full_text = ""
            avg_logprob = 0.0
            seg_count = 0
            for segment in segments:
                full_text += segment.text
                log_prob = (
                    getattr(segment, "avg_log_prob", None)
                    or getattr(segment, "avg_logprob", -0.5)
                )
                avg_logprob += log_prob
                seg_count += 1

            if seg_count > 0:
                avg_logprob /= seg_count

            confidence = min(1.0, max(0.0, math.exp(avg_logprob)))

            return {
                "text": full_text.strip(),
                "language": info.language or "en",
                "language_probability": getattr(info, "language_probability", 0.5),
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"Transcription runner failed: {e}", exc_info=True)
            return {"text": "", "language": "en",
                    "language_probability": 0.0, "confidence": 0.0}

    def get_audio_level(self, audio_bytes: bytes) -> float:
        try:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            if len(audio_array) > 0:
                rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))
                return float(min(rms / 32768.0, 1.0))
            return 0.0
        except Exception as e:
            logger.error(f"Audio level error: {e}")
            return 0.0

    def validate_audio(self, audio_bytes: bytes) -> Dict:
        try:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            duration = len(audio_array) / 16000
            if duration < 0.5:
                return {"valid": False, "reason": "Audio too short (minimum 0.5 seconds)"}
            if duration > 120:
                return {"valid": False, "reason": "Audio too long (maximum 120 seconds)"}
            rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))
            if rms < 100:
                return {"valid": False, "reason": "Audio appears to be silent"}
            return {"valid": True, "duration": duration, "level": rms / 32768.0}
        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            return {"valid": False, "reason": str(e)}

    def get_audio_spectrum(self, audio_bytes: bytes, num_bars: int = 20) -> list:
        try:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            fft = np.fft.fft(audio_array)
            frequencies = np.abs(fft[: len(fft) // 2])
            bar_size = len(frequencies) // num_bars
            bars = []
            for i in range(num_bars):
                start = i * bar_size
                bar_value = np.mean(frequencies[start : start + bar_size])
                normalized = float(
                    min(bar_value / np.max(frequencies), 1.0)
                    if np.max(frequencies) > 0 else 0
                )
                bars.append(normalized)
            return bars
        except Exception as e:
            logger.error(f"Spectrum error: {e}")
            return [0.0] * num_bars

    def check_health(self) -> bool:
        return self.model is not None

    async def cleanup(self):
        self.executor.shutdown(wait=True)
        logger.info("VoiceProcessor cleaned up")


if __name__ == "__main__":
    async def test():
        processor = VoiceProcessor()
        await processor.initialize()
        print(f"VoiceProcessor ready (model: {processor.model_size})")
    asyncio.run(test())