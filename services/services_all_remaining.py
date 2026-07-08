"""
Remaining Core Services
TTS (edge-tts neural voices), Translation (offline), Vision, Emergency Detection
"""

# ===== TTS Engine (edge-tts — near-human Hindi/Punjabi/English) =====
import asyncio
import edge_tts
import os
import requests
from datetime import datetime
from utils.utils_logger import setup_logger
from dotenv import load_dotenv
import re

load_dotenv()
logger = setup_logger(__name__)


class TTSEngine:
    """Text-to-Speech with edge-tts neural voices.
    
    Uses Microsoft Edge's neural TTS voices:
    - Hindi: hi-IN-SwaraNeural (female) / hi-IN-MadhurNeural (male)
    - Punjabi: pa-IN-GurpreetNeural (male)
    - English: en-IN-NeerjaNeural (Indian English female)
    
    These voices natively speak Hindi and Punjabi with correct pronunciation —
    no transliteration needed.
    """

    # Voice mapping: language code → (primary voice, fallback voice)
    # Note: pa-IN (Punjabi) voices are NOT available in edge-tts.
    # Hindi voice works well for Punjabi since they're linguistically close.
    VOICES = {
        "hi": ("hi-IN-SwaraNeural", "hi-IN-MadhurNeural"),
        "pa": ("hi-IN-SwaraNeural", "hi-IN-MadhurNeural"),  # Punjabi → Hindi voice (best available)
        "en": ("en-IN-NeerjaNeural", "en-IN-PrabhatNeural"),
    }
    # Default voice for unknown languages
    DEFAULT_VOICE = "en-IN-NeerjaNeural"

    def __init__(self):
        self.audio_dir = "static/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        # Initialize ElevenLabs config for Punjabi TTS
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        # Default to a good starting voice if they don't provide a custom one (e.g., Bella/Rachel)
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
        logger.info("TTS Engine initialized (edge-tts for en/hi, ElevenLabs for pa)")

    async def initialize(self):
        """Validate edge-tts works. Downloads voice list on first run."""
        try:
            voices = await edge_tts.list_voices()
            available = {v["ShortName"] for v in voices}
            for lang, (primary, fallback) in self.VOICES.items():
                if primary in available:
                    logger.info(f"  TTS voice OK: {primary} ({lang})")
                else:
                    logger.warning(f"  TTS voice NOT FOUND: {primary} ({lang})")
            logger.info("TTS Engine ready (edge-tts)")
        except Exception as e:
            logger.warning(f"TTS init check failed: {e}")

    def _detect_text_language(self, text: str, language_hint: str) -> str:
        """Detect language from text script to pick the right voice."""
        # If hint is already hi/pa/en, trust it
        if language_hint in self.VOICES:
            return language_hint

        # Script-based detection
        has_devanagari = any('\u0900' <= ch <= '\u097F' for ch in text)
        has_gurmukhi = any('\u0A00' <= ch <= '\u0A7F' for ch in text)

        if has_gurmukhi:
            return "pa"
        if has_devanagari:
            return "hi"
        return "en"

    async def generate_speech(
        self,
        text: str,
        language: str,
        patient_id: str,
        session_id: str,
    ) -> str:
        """
        Generate speech audio using edge-tts neural voice.

        PUNJABI FIX:
        - When language == "pa" and no ElevenLabs key is set, we use the Hindi
          voice (linguistically very close). BUT edge-tts Hindi voice CANNOT speak
          Gurmukhi Unicode characters — it will fail or produce silence.
        - Fix: if the response text contains Gurmukhi script, transliterate it by
          stripping Gurmukhi and prepending a short English/Hindi intro so the TTS
          still produces something audible rather than failing silently.
        - Always verify the output file exists and has non-zero size before returning
          the URL — return None only as a true last resort.
        """
        try:
            # Detect the actual text language (handles mixed-script responses)
            actual_lang = self._detect_text_language(text, language)
            logger.info(f"TTS request: hint={language!r} actual={actual_lang!r} text_len={len(text)}")

            # Pick voice
            voice = self.VOICES.get(actual_lang, (self.DEFAULT_VOICE,))[0]

            # ── Prepare speak_text ────────────────────────────────────
            speak_text = text

            # Truncate very long texts
            if len(speak_text) > 2000:
                speak_text = speak_text[:1800] + "... Please read the full response on screen."

            # Strip markdown symbols
            speak_text = re.sub(r'[*#_~>`]+', '', speak_text)

            # PUNJABI EDGE-TTS FIX:
            # If actual_lang is "pa" and we'll use a Hindi edge-tts voice,
            # strip Gurmukhi characters — edge-tts Hindi voice cannot read them
            # and will produce an error or empty audio file.
            # Replace Gurmukhi runs with a short Hindi intro so something is spoken.
            if actual_lang == "pa" and not self.elevenlabs_key:
                has_gurmukhi = any('\u0A00' <= ch <= '\u0A7F' for ch in speak_text)
                if has_gurmukhi:
                    logger.info("Gurmukhi detected in TTS text — stripping for edge-tts Hindi voice.")
                    # Remove Gurmukhi characters, collapse whitespace
                    speak_text_cleaned = re.sub(r'[\u0A00-\u0A7F]+', ' ', speak_text).strip()
                    speak_text_cleaned = re.sub(r'\s{2,}', ' ', speak_text_cleaned)
                    # If stripping left nothing, use a safe fallback phrase
                    if not speak_text_cleaned or len(speak_text_cleaned) < 10:
                        speak_text_cleaned = (
                            "Aapka jawab screen par dikhaya gaya hai. "
                            "Kripya screen par padhen."
                        )
                    speak_text = speak_text_cleaned

            # Build output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename  = f"{patient_id}_{timestamp}.mp3"
            filepath  = os.path.join(self.audio_dir, filename)

            # ── Route to ElevenLabs for Punjabi (if key available) ───
            if actual_lang == "pa" and self.elevenlabs_key:
                logger.info("Using ElevenLabs TTS for Punjabi (eleven_multilingual_v2).")
                url     = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
                headers = {
                    "Accept":        "audio/mpeg",
                    "Content-Type":  "application/json",
                    "xi-api-key":    self.elevenlabs_key,
                }
                payload = {
                    "text":       speak_text,
                    "model_id":   "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                }

                def _fetch_elevenlabs():
                    resp = requests.post(url, json=payload, headers=headers, timeout=30)
                    resp.raise_for_status()
                    with open(filepath, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)

                try:
                    await asyncio.to_thread(_fetch_elevenlabs)
                    logger.info(f"ElevenLabs TTS OK: {filename}")
                except Exception as elabs_err:
                    logger.error(f"ElevenLabs TTS failed: {elabs_err}. Falling back to edge-tts.")
                    communicate = edge_tts.Communicate(speak_text, voice)
                    await communicate.save(filepath)

            else:
                # ── edge-tts for English, Hindi, and Punjabi fallback ──
                if actual_lang == "pa":
                    logger.info(
                        f"No ELEVENLABS_API_KEY — using edge-tts Hindi voice for Punjabi. "
                        f"speak_text preview: {speak_text[:80]!r}"
                    )
                communicate = edge_tts.Communicate(speak_text, voice)
                await communicate.save(filepath)

            # ── Verify output file is valid ───────────────────────────
            if not os.path.exists(filepath):
                logger.error(f"TTS output file missing: {filepath}")
                return None

            file_size = os.path.getsize(filepath)
            if file_size < 512:   # less than 512 bytes = almost certainly empty/corrupt
                logger.error(f"TTS output file too small ({file_size} bytes): {filepath}")
                # Try once more with a safe English fallback
                safe_text = "Your response is shown on screen. Please read it there."
                fallback_voice = self.VOICES["en"][0]
                communicate = edge_tts.Communicate(safe_text, fallback_voice)
                await communicate.save(filepath)
                file_size = os.path.getsize(filepath)
                if file_size < 512:
                    logger.error("Fallback TTS also failed — giving up.")
                    return None
                logger.info(f"Fallback English TTS saved: {file_size} bytes")

            logger.info(f"TTS audio ready: {filename} ({file_size} bytes, lang={actual_lang})")
            return f"/api/audio/{filename}"

        except Exception as e:
            logger.error(f"TTS generation error: {e}", exc_info=True)
            return None

    def check_health(self) -> bool:
        return os.path.exists(self.audio_dir)


# ===== Translation Service (offline — LLM handles multilingual) =====
from langdetect import detect


class TranslationService:
    """
    Offline language detection service.
    
    Translation is handled by the LLM itself (Llama 3.1 is multilingual).
    This service only provides language detection via langdetect (offline).
    """
    
    SUPPORTED = {"en": "English", "hi": "Hindi", "pa": "Punjabi"}
    
    def __init__(self):
        logger.info("Translation Service initialized (offline — LLM multilingual)")
    
    def detect_language(self, text: str) -> str:
        """Detect text language (offline, uses langdetect)."""
        try:
            lang = detect(text)
            if lang in self.SUPPORTED:
                return lang
            return "en"
        except Exception:
            return "en"
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Pass-through — LLM handles multilingual directly."""
        return text
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Pass-through — LLM responds in patient's language."""
        return text


# ===== Vision Analyzer =====
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, ImageStat, ImageFilter
import torch
import io
import hashlib


class VisionAnalyzer:
    """Medical image analysis with BLIP + intelligent medical context"""
    
    def __init__(self):
        self.processor = None
        self.model = None
        logger.info("Vision Analyzer initialized")
    
    async def initialize(self):
        """Load vision model"""
        try:
            logger.info("Loading BLIP image captioning model...")
            self.processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            logger.info("BLIP image captioning model loaded")
        except Exception as e:
            logger.warning(f"Vision model load failed: {e}")
            logger.warning("Image analysis will use fallback (LLM-only mode)")

    def _analyze_image_properties(self, image: Image.Image) -> dict:
        """Analyze image pixel properties to detect X-ray vs photo vs report"""
        w, h = image.size
        stat = ImageStat.Stat(image)
        means = stat.mean  # per-channel means
        stddevs = stat.stddev
        
        gray = image.convert("L")
        gray_stat = ImageStat.Stat(gray)
        gray_mean = gray_stat.mean[0]
        gray_std = gray_stat.stddev[0]
        
        # Detect if image is predominantly grayscale (X-ray/CT/MRI)
        if len(means) >= 3:
            r, g, b = means[0], means[1], means[2]
            color_spread = max(abs(r-g), abs(r-b), abs(g-b))
            is_grayscale = color_spread < 20
        else:
            is_grayscale = True
            color_spread = 0
        
        # X-rays: typically grayscale, high contrast, dark background
        is_xray_like = is_grayscale and gray_std > 40 and gray_mean < 140
        
        # Text-heavy (reports): lots of high-contrast edges, mostly white
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_mean = edge_stat.mean[0]
        is_document = gray_mean > 180 and edge_mean > 15
        
        return {
            "width": w, "height": h,
            "is_grayscale": is_grayscale,
            "is_xray_like": is_xray_like,
            "is_document": is_document,
            "gray_mean": gray_mean,
            "gray_std": gray_std,
            "color_spread": color_spread,
            "aspect_ratio": round(w / max(h, 1), 2),
        }

    def _classify_image_type(self, props: dict, image_type_hint: str = None) -> str:
        """Classify the image into medical categories"""
        if image_type_hint and image_type_hint != "photo":
            return image_type_hint
        if props["is_document"]:
            return "document_report"
        if props["is_xray_like"]:
            return "xray_scan"
        return "clinical_photo"

    async def analyze_medical_image(self, image_bytes: bytes, 
                                      body_region: str = None, 
                                      image_type: str = None) -> dict:
        """Analyze medical image with intelligent type detection, trying local model first and falling back to Gemini"""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            props = self._analyze_image_properties(image)
            classified_type = self._classify_image_type(props, image_type)
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            props = {"width": 0, "height": 0, "is_grayscale": False, "is_xray_like": False, "is_document": False}
            classified_type = image_type or "photo"

        # 1. Try local BLIP image captioning model
        try:
            if self.model is None or self.processor is None:
                await self.initialize()
            
            if self.model is not None and self.processor is not None:
                # Choose prompt based on detected type
                if classified_type == "xray_scan":
                    prompts = [
                        "an x-ray image showing",
                        "a medical radiograph of",
                    ]
                elif classified_type == "document_report":
                    prompts = [
                        "a medical document showing",
                    ]
                else:
                    prompts = [
                        "a medical photograph showing",
                        "a clinical image of",
                    ]

                captions = []
                
                # Unconditional caption
                inputs = self.processor(images=image, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                output = self.model.generate(**inputs, max_new_tokens=100)
                base_caption = self.processor.decode(output[0], skip_special_tokens=True)
                captions.append(base_caption)

                # Conditional captions with medical prompts
                for prompt in prompts:
                    inputs2 = self.processor(images=image, text=prompt, return_tensors="pt")
                    if torch.cuda.is_available():
                        inputs2 = {k: v.cuda() for k, v in inputs2.items()}
                    output2 = self.model.generate(**inputs2, max_new_tokens=100)
                    cap = self.processor.decode(output2[0], skip_special_tokens=True)
                    if cap and cap not in captions:
                        captions.append(cap)

                # Build rich description with context
                region_text = f" of the {body_region.replace('_',' ')} region" if body_region else ""
                type_label = {
                    "xray_scan": "X-ray/radiological scan",
                    "document_report": "medical document/report",
                    "clinical_photo": "clinical photograph",
                }.get(classified_type, "medical image")

                description = (
                    f"[Image Type: {type_label}{region_text}] "
                    f"Visual analysis: {'. '.join(captions)}. "
                    f"Image properties: {'grayscale' if props.get('is_grayscale') else 'color'}, "
                    f"resolution {props.get('width')}x{props.get('height')}."
                )

                logger.info(f"Local vision analysis ({classified_type}): {description[:120]}")
                return {
                    "description": description,
                    "image_type": classified_type,
                    "properties": props,
                    "captions": captions,
                    "confidence": 0.8
                }
        except Exception as local_err:
            logger.warning(f"Local image analysis failed: {local_err}. Falling back to Gemini API.")

        # 2. Fallback to Gemini Vision API
        logger.info("Using Gemini Vision API fallback...")
        gemini_res = await self._analyze_with_gemini(image_bytes, props, classified_type, body_region)
        if gemini_res:
            return gemini_res

        # 3. Final default fallback if everything fails
        region_text = f" of the {body_region.replace('_',' ')} region" if body_region else ""
        type_label = {
            "xray_scan": "X-ray/radiological scan",
            "document_report": "medical document/report",
            "clinical_photo": "clinical photograph",
        }.get(classified_type, "medical image")
        return {
            "description": f"[Image Type: {type_label}{region_text}] Image received. Vision service is currently offline — please describe what you see in detail.",
            "image_type": classified_type,
            "properties": props,
            "confidence": 0.2
        }

    async def _analyze_with_gemini(self, image_bytes: bytes, props: dict, classified_type: str, body_region: str = None) -> dict:
        """Call Gemini API for vision analysis"""
        import base64
        import httpx
        import json

        api_key = os.getenv("GOOGLE_AI_API_KEY", "").strip()
        if not api_key:
            logger.warning("Gemini Vision fallback requested but GOOGLE_AI_API_KEY is missing.")
            return None

        # Build prompt
        region_text = f" of the {body_region.replace('_',' ')} region" if body_region else ""
        type_label = {
            "xray_scan": "X-ray/radiological scan",
            "document_report": "medical document/report",
            "clinical_photo": "clinical photograph",
        }.get(classified_type, "medical image")

        prompt = (
            f"Analyze this medical image ({type_label}{region_text}). "
            "Provide a highly detailed, professional medical visual analysis describing what is visible in the image. "
            "Identify and describe key structures, features, and visual characteristics. "
            "Keep the analysis highly professional, detailed, objective, and clear."
        )

        encoded_data = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": encoded_data
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800},
        }

        model_candidates = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
        last_err = None

        async with httpx.AsyncClient(timeout=120) as client:
            for model in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        parts = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        text_result = "".join(part.get("text", "") for part in parts).strip()
                        if text_result:
                            description = (
                                f"[Image Type: {type_label}{region_text}] "
                                f"Visual analysis (Gemini): {text_result} "
                                f"Image properties: {'grayscale' if props.get('is_grayscale') else 'color'}, "
                                f"resolution {props.get('width')}x{props.get('height')}."
                            )
                            logger.info(f"Gemini Vision ({model}) successfully analyzed image")
                            return {
                                "description": description,
                                "image_type": classified_type,
                                "properties": props,
                                "confidence": 0.95
                            }
                    else:
                        logger.warning(f"Gemini Vision model {model} failed with status {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Error calling Gemini Vision model {model}: {e}")
                    last_err = e
                    continue

        if last_err:
            logger.error(f"Gemini Vision fallback failed: {last_err}")
        return None

    
    def check_health(self) -> bool:
        return True


# ===== Emergency Detector (offline keyword matching) =====
class EmergencyDetector:
    """Emergency symptom detection — fully offline keyword matching"""
    
    EMERGENCY_KEYWORDS = [
        # English — Cardiac
        "chest pain", "chest tightness", "heart attack", "crushing pain",
        # English — Respiratory
        "can't breathe", "cannot breathe", "difficulty breathing",
        "shortness of breath", "breathless", "choking",
        # English — Neurological
        "stroke", "face drooping", "can't move", "paralyzed",
        "severe headache", "worst headache", "unconscious", "passed out",
        # English — Bleeding/Trauma
        "severe bleeding", "heavy bleeding", "won't stop bleeding",
        "severe injury", "broken bone",
        # English — Other
        "suicide", "kill myself", "severe pain", "unbearable pain",
        "allergic reaction", "swelling throat", "anaphylaxis",
        # Hindi
        "सीने में दर्द", "सांस नहीं आ रही", "दिल का दौरा",
        "बेहोश", "खून बंद नहीं हो रहा", "बहुत तेज दर्द",
        "आत्महत्या", "मर जाना चाहता",
        # Punjabi
        "ਛਾਤੀ ਵਿੱਚ ਦਰਦ", "ਸਾਹ ਨਹੀਂ ਆ ਰਿਹਾ", "ਦਿਲ ਦਾ ਦੌਰਾ",
        "ਬੇਹੋਸ਼", "ਬਹੁਤ ਤੇਜ਼ ਦਰਦ",
    ]
    
    def check_emergency(self, text: str) -> dict:
        """Check if text indicates emergency"""
        text_lower = text.lower()
        
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return {
                    "is_emergency": True,
                    "reason": keyword,
                    "response": self._get_emergency_response(keyword)
                }
        
        return {"is_emergency": False}
    
    def _get_emergency_response(self, keyword: str) -> str:
        """Get appropriate emergency response"""
        return f"""🚨 MEDICAL EMERGENCY DETECTED

Your symptoms suggest a potentially serious medical emergency.

IMMEDIATE ACTIONS:
1. Call emergency services NOW (911 or local emergency number)
2. Do NOT wait or delay
3. If someone is with you, alert them immediately
4. Stay calm and follow emergency operator instructions

This is a life-threatening situation that requires immediate professional medical care. AI cannot replace emergency medical services.

If you're having a medical emergency, please hang up and call 911 immediately."""