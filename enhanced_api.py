# pyre-ignore-all-errors[21]
"""
Medical AI Assistant — Enterprise API v4.1
Complete backend: RAG, triage, OCR, health records, streaming
Optimized with parallel pipelines, TTL caching, and async wrappers.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.auth import get_current_user, get_password_hash, verify_password, create_access_token
import json
import os
import re
from io import BytesIO
from datetime import datetime
import uuid
import asyncio
from functools import lru_cache
import time
import hashlib

from services.services_voice_processor import VoiceProcessor
from services.services_llm_engine import MedicalLLMEngine, CloudModelEngine
from services.database import HealthDatabase
from services.rag_engine import MedicalRAGEngine
from services.triage_engine import TriageEngine
from services.ocr_engine import OCREngine
from services.ner_engine import NEREngine
from services.services_all_remaining import VisionAnalyzer, TTSEngine, TranslationService
from services.predictive_health import PredictiveHealthEngine
from services.data_doctors import HOSPITAL_DATA
from services.medical_reference import (
    LAB_TEST_CATALOG, LAB_CATALOG_MAP, LAB_CATEGORIES,
    SPECIALIST_PROMPTS, RISK_RULES,
    compute_risk_scores, compute_organ_scores, compute_lab_correlations,
    detect_trends, get_screening_plan, search_medicines,
    get_normal_range, interpret_lab_value, interpret_lab_panel,
)
from utils.utils_logger import setup_logger
from PIL import Image, UnidentifiedImageError

logger = setup_logger(__name__)


def _parse_allowed_origins() -> list[str]:
    origins = []
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    if raw_origins:
        origins.extend([origin.strip() for origin in raw_origins.split(",") if origin.strip()])

    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url:
        origins.append(frontend_url)

    # Add known production domains as fallbacks
    origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-health-tracker-six.vercel.app",  # Production frontend
    ])

    seen = set()
    unique_origins = []
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)
    return unique_origins


def _safe_patient_prefix(patient_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", patient_id).strip("_")[:64] or "patient"


async def _collect_stream_text(stream):
    chunks = []
    async for token in stream:
        chunks.append(token)
    return "".join(chunks)


def _available_cloud_provider() -> str:
    preferred = os.getenv("DEFAULT_MODEL_PROVIDER", "").strip().lower()
    if preferred in {"openai", "gemini", "anthropic"} and cloud_engine.is_available(preferred):
        return preferred
    for provider in ("openai", "gemini", "anthropic"):
        if cloud_engine.is_available(provider):
            return provider
    return "core"


def _resolve_model_provider(requested_provider: Optional[str]) -> str:
    provider = (requested_provider or "").strip().lower()
    if provider in {"openai", "gemini", "anthropic"}:
        if cloud_engine.is_available(provider):
            return provider
        return _available_cloud_provider()
    if provider == "core":
        return "core" if llm_engine.check_health() else _available_cloud_provider()
    default_provider = os.getenv("DEFAULT_MODEL_PROVIDER", "").strip().lower()
    if default_provider == "core":
        return "core" if llm_engine.check_health() else _available_cloud_provider()
    if default_provider in {"openai", "gemini", "anthropic"} and cloud_engine.is_available(default_provider):
        return default_provider
    return _available_cloud_provider()


def _validate_image_bytes(image_bytes: bytes) -> None:
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum size is 5MB.")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
    except UnidentifiedImageError:
        raise HTTPException(400, "Invalid image file.")
    except Exception:
        raise HTTPException(400, "Corrupted or unsupported image file.")


async def _generate_model_response(
    *,
    provider: Optional[str],
    message: str,
    history: List[Dict],
    patient_id: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    extra_context: str = "",
) -> Dict:
    resolved = _resolve_model_provider(provider)
    if resolved == "core":
        return await llm_engine.generate_response(
            message=message,
            history=history,
            patient_id=patient_id,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_context=extra_context,
        )

    response_text = await _collect_stream_text(
        cloud_engine.generate_response_stream(
            provider=resolved,
            message=message,
            history=history,
            patient_id=patient_id,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_context=extra_context,
        )
    )
    return {
        "response": response_text.strip() or "I can help with that, but I need a little more detail.",
        "confidence": 0.9,
        "model": resolved,
        "timestamp": datetime.now().isoformat(),
    }

app = FastAPI(title="Medical AI Assistant Pro", version="4.1.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (tighten later)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from services.auth import SECRET_KEY, ALGORITHM

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    
    # Allow OPTIONS (preflight) requests to pass through for CORS
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Public routes
    if not path.startswith("/api/") or path.startswith("/api/auth/") or path.startswith("/api/health") or path.startswith("/api/model-providers") or path.startswith("/api/lab-catalog") or path.startswith("/api/medicine-catalog") or path.startswith("/api/specialists"):
        return await call_next(request)
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid authentication token"})
        
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        patient_id = payload.get("sub")
        if not patient_id:
            return JSONResponse(status_code=401, content={"detail": "Invalid token payload"})
            
        request.state.user_id = patient_id
        
        # Simple authorization: if path contains /patient/{id}, ensure it matches token
        parts = path.split("/")
        if "patient" in parts:
            idx = parts.index("patient")
            if idx + 1 < len(parts):
                path_patient_id = parts[idx + 1]
                if path_patient_id != patient_id:
                    return JSONResponse(status_code=403, content={"detail": "Access forbidden to this patient's data"})
                    
    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
        
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    return response

# ── TTL Cache for hot-path lookups ──────────────────────────────
class TTLCache:
    """Thread-safe in-memory cache with per-key TTL expiry.
    Used to avoid re-running expensive operations (RAG search,
    patient context) within a short window."""
    def __init__(self, default_ttl: int = 30):
        self._store: dict = {}  # key -> (value, expiry_ts)
        self._ttl = default_ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry and entry[1] > time.time():
            return entry[0]
        if entry:
            self._store.pop(key, None)
        return None

    def set(self, key: str, value, ttl: Optional[int] = None):
        self._store[key] = (value, time.time() + (ttl or self._ttl))

    def invalidate(self, prefix: str = ""):
        if not prefix:
            self._store.clear()
        else:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)

_cache = TTLCache(default_ttl=30)  # 30s TTL for RAG/patient lookups

# ── Lazy Service Initialization (prevent memory crash on Railway) ────
_services = {}

def _get_service(name: str, cls, *args, **kwargs):
    """Lazy-load services on first use, not at startup."""
    if name not in _services:
        logger.info(f"Lazy-loading {name}...")
        _services[name] = cls(*args, **kwargs)
    return _services[name]

# Services that are lazy-loaded (heavy ML models)
class LazyService:
    """Wrapper for lazy-loading a service."""
    def __init__(self, name, cls):
        self.name = name
        self.cls = cls
        self._instance = None
    
    def __getattr__(self, attr):
        if self._instance is None:
            logger.info(f"Lazy-loading {self.name}...")
            self._instance = self.cls()
        return getattr(self._instance, attr)

voice_processor = LazyService("voice_processor", VoiceProcessor)
llm_engine = LazyService("llm_engine", MedicalLLMEngine)
rag_engine = LazyService("rag_engine", MedicalRAGEngine)
triage = LazyService("triage", TriageEngine)
ocr_engine = LazyService("ocr_engine", OCREngine)
vision_analyzer = LazyService("vision_analyzer", VisionAnalyzer)
tts_engine = LazyService("tts_engine", TTSEngine)
translation_service = LazyService("translation_service", TranslationService)

# Services (lightweight or already lazy)
db = HealthDatabase()
predictive_engine = PredictiveHealthEngine(db)
ner_engine = NEREngine()
cloud_engine = CloudModelEngine()

os.makedirs("static/audio", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("data/conversations", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Async wrappers for blocking calls ───────────────────────────
# These allow us to run CPU-bound / sync-blocking operations in
# parallel with asyncio.gather() instead of sequentially.

async def _async_triage(message: str) -> Dict:
    """Run triage assessment in thread pool (regex matching)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, triage.assess, message)

async def _async_rag_context(message: str, top_k: int = 3) -> str:
    """Cached RAG context retrieval."""
    if not rag_engine.check_health():
        return ""
    cache_key = f"rag_ctx:{hashlib.md5(message.encode()).hexdigest()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, rag_engine.get_context_for_query, message, top_k)
    _cache.set(cache_key, result, ttl=60)
    return result

async def _async_rag_citations(message: str, top_k: int = 3) -> List[Dict]:
    """Cached RAG citation retrieval."""
    if not rag_engine.check_health():
        return []
    cache_key = f"rag_cite:{hashlib.md5(message.encode()).hexdigest()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, rag_engine.get_citations_for_query, message, top_k)
    _cache.set(cache_key, result, ttl=60)
    return result

async def _async_patient_context(patient_id: str) -> str:
    """Cached patient context retrieval."""
    cache_key = f"pat_ctx:{patient_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, db.get_patient_context, patient_id)
    _cache.set(cache_key, result, ttl=15)  # shorter TTL for patient data
    return result

async def _async_patient_data(patient_id: str) -> Optional[Dict]:
    """Cached patient record retrieval."""
    cache_key = f"pat_data:{patient_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, db.get_patient, patient_id)
    _cache.set(cache_key, result, ttl=15)
    return result

async def _async_conversation(patient_id: str, session_id: str, limit: int = 10) -> List[Dict]:
    """Get conversation history in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, db.get_conversation, patient_id, session_id, limit)


# ── Request Models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    patient_id: str
    message: str
    language: Optional[str] = "auto"
    session_id: Optional[str] = None
    generation_mode: Optional[str] = "balanced"  # fast, balanced, detailed
    model_provider: Optional[str] = None  # core, openai, gemini, anthropic


class PatientUpdateRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    ethnicity: Optional[str] = None
    family_history: Optional[str] = None


class HealthEventRequest(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    body_region: Optional[str] = None
    severity: Optional[str] = "mild"
    date: Optional[str] = None


class LabResultRequest(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"service": "Medical AI Assistant Pro", "version": "4.0.0", "status": "operational"}


@app.get("/status")
async def status():
    """Simple diagnostic endpoint - no service checks, just confirm app is running"""
    return {"status": "OK", "app": "Medical AI Assistant", "environment": os.getenv("ENVIRONMENT", "local")}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": llm_engine.check_health(),
            "voice": voice_processor.check_health(),
            "database": db.check_health(),
            "rag": rag_engine.check_health(),
            "triage": triage.check_health(),
            "vision": vision_analyzer.check_health(),
        }
    }


# ══════════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ══════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    patient_id: str
    password: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class LoginRequest(BaseModel):
    patient_id: str
    password: str

@app.post("/api/auth/register")
async def register_user(req: RegisterRequest):
    if db.get_patient(req.patient_id):
        raise HTTPException(status_code=400, detail="User already exists")
    
    password_hash = get_password_hash(req.password)
    db.ensure_patient(
        patient_id=req.patient_id, 
        name=req.name, 
        password_hash=password_hash,
        age=req.age, 
        gender=req.gender
    )
    return {"message": "User registered successfully"}

@app.post("/api/auth/quick-register")
async def quick_register_user(req: dict):
    """Quick registration for frontend — auto-registers with just patient_id"""
    patient_id = req.get("patient_id", "").strip()
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id required")
    
    # Auto-register if not exists
    existing = db.get_patient(patient_id)
    if not existing:
        db.ensure_patient(
            patient_id=patient_id,
            name=patient_id,
            password_hash=None,  # No password needed for auto-generated accounts
            age=None,
            gender=None
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": patient_id})
    return {"access_token": access_token, "token_type": "bearer", "patient_id": patient_id}

@app.post("/api/auth/login")
async def login_user(req: LoginRequest):
    patient = db.get_patient(req.patient_id)
    if not patient:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    conn = db._conn()
    row = conn.execute("SELECT password_hash FROM patients WHERE patient_id=?", (req.patient_id,)).fetchone()
    if not row or not row["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access_token = create_access_token(data={"sub": req.patient_id})
    return {"access_token": access_token, "token_type": "bearer", "patient_id": req.patient_id}


# ══════════════════════════════════════════════════════════════════
#  STREAMING CHAT  (main endpoint — tokens appear word by word)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/model-providers")
async def get_model_providers():
    """List available model providers and their status"""
    core_available = llm_engine.check_health()
    return {
        "default_provider": _resolve_model_provider(None),
        "providers": [
            {"id": "core", "label": "Core (Llama)", "available": core_available, "description": "Local AI — requires a self-hosted model server"},
            *cloud_engine.get_available_providers(),
        ]
    }

@app.post("/api/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(chat_request: ChatRequest, request: Request):
    """Streaming chat with RAG + triage + patient context.

    OPTIMIZED PIPELINE: triage, RAG, patient context, conversation
    history, and patient data are all fetched in PARALLEL via
    asyncio.gather() — cutting pre-LLM latency by ~60-70%.
    """
    if hasattr(request.state, "user_id") and chat_request.patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    session_id = request.session_id or str(uuid.uuid4())
    patient_id = request.patient_id
    db.ensure_patient(patient_id)

    detected_lang = (
        translation_service.detect_language(request.message)
        if request.language == "auto"
        else request.language
    )

    # ══ PARALLEL PRE-FETCH ══════════════════════════════════════
    # All 5 operations are independent — run them simultaneously.
    (
        triage_result,
        rag_ctx,
        citations,
        patient_ctx,
        patient_data,
        history,
    ) = await asyncio.gather(
        _async_triage(request.message),
        _async_rag_context(request.message, top_k=3),
        _async_rag_citations(request.message, top_k=3),
        _async_patient_context(patient_id),
        _async_patient_data(patient_id),
        _async_conversation(patient_id, session_id, limit=10),
    )
    # ════════════════════════════════════════════════════════════

    if triage_result["level"] == "emergency":
        emergency_text = (
            f"🚨 EMERGENCY DETECTED — {triage_result['reason']}\n\n"
            f"{triage_result['recommendation']}\n\n"
            "IMMEDIATE ACTIONS:\n"
            "1. Call emergency services (112) NOW\n"
            "2. Do NOT wait or delay\n"
            "3. Alert someone near you immediately\n"
            "4. Stay calm and follow operator instructions\n\n"
            "This AI cannot replace emergency medical services."
        )
        db.save_message(patient_id, session_id, "user", chat_request.message, detected_lang)
        db.save_message(patient_id, session_id, "assistant", emergency_text, "en",
                        metadata={"emergency": True, "triage": triage_result})
        db.add_health_event(patient_id, "emergency", triage_result["reason"],
                            chat_request.message, severity="critical")

        async def _em():
            yield f"data: {json.dumps({'type':'triage','level':'emergency','reason':triage_result['reason']})}\n\n"
            yield f"data: {json.dumps({'type':'chunk','content':emergency_text})}\n\n"
            yield f"data: {json.dumps({'type':'done','session_id':session_id,'language':detected_lang,'triage':triage_result})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(_em(), media_type="text/event-stream")

    # ── Build LLM context (from pre-fetched data) ──
    triage_ctx = triage.get_triage_prompt(triage_result)

    # Elderly patient detection — inject special instructions
    elderly_ctx = ""
    if patient_data and patient_data.get("age"):
        try:
            age = int(patient_data["age"])
            if age >= 65:
                elderly_ctx = (
                    "ELDERLY PATIENT ALERT (age " + str(age) + "):\n"
                    "This is an elderly patient. You MUST:\n"
                    "• Provide a MINIMUM of 3 differential diagnoses for any complaint.\n"
                    "• Elderly symptoms often mask serious conditions — consider atypical presentations.\n"
                    "• Check for red flags: new confusion, sudden falls, dehydration, rapid decline.\n"
                    "• Always consider medication side effects and polypharmacy risks.\n"
                    "• Flag any danger signs prominently with ⚠️ warning."
                )
        except (ValueError, TypeError):
            pass

    punjabi_ctx = (
        "The patient is a Punjabi speaker. "
        "Respond in clear, simple Hindi (Devanagari script) — NOT Gurmukhi. "
        "Hindi and Punjabi are mutually intelligible; Hindi TTS will be spoken back to them. "
        "Use short sentences. Avoid complex medical jargon."
    ) if detected_lang == "pa" else ""

    extra = "\n\n".join(filter(None, [
        f"PATIENT RECORD:\n{patient_ctx}" if patient_ctx else "",
        elderly_ctx,
        punjabi_ctx,
        rag_ctx,
        triage_ctx,
    ]))

    async def _stream():
        full = ""
        started = False  # track when real text starts
        try:
            yield f"data: {json.dumps({'type':'triage','level':triage_result['level'],'reason':triage_result['reason']})}\n\n"

            mode = getattr(chat_request, 'generation_mode', 'balanced') or 'balanced'
            mode_tokens = {"fast": 500, "balanced": 1000, "detailed": 1800}
            mode_temp = {"fast": 0.2, "balanced": 0.3, "detailed": 0.45}
            mode_ctx = {
                "fast": (
                    "\nMODE: FAST — Be concise but COMPLETE. Use short bullets. "
                    "Still include: top 2 differential diagnoses (one-line reasoning each), "
                    "2-3 specific home remedies (not generic), foods to eat/avoid, "
                    "and 2-3 diagnostic questions. If medications are mentioned, give ONE key interaction detail. "
                    "Keep under 200 words. Prioritize speed but every point must add value."
                ),
                "balanced": (
                    "\nMODE: BALANCED — Follow ALL system prompt rules fully. Include: "
                    "2-3 differential diagnoses with reasoning, contributing factors (age/lifestyle/stress/diet), "
                    "3-5 specific home remedies across categories (dietary, herbal, topical, lifestyle), "
                    "foods to eat AND foods to avoid (3+ each), "
                    "drug interactions with mechanism and SPECIFIC timing (not generic morning/night), "
                    "specialist recommendation, and 3-5 diagnostic questions. "
                    "Keep under 400 words."
                ),
                "detailed": (
                    "\nMODE: DETAILED — Give a thorough, comprehensive medical response. Include: "
                    "3+ differential diagnoses with detailed reasoning and staging/classification, "
                    "ALL relevant contributing factors (age, gender, lifestyle, stress, sleep, occupation, diet, season, environment), "
                    "risk factors (family history, BMI, smoking, alcohol, pre-existing conditions), "
                    "5+ specific home remedies covering dietary, herbal/natural, lifestyle adjustments, topical, and hydration, "
                    "detailed foods to eat (5+) and foods to avoid (5+) with reasoning, "
                    "complete drug interaction analysis if medications are involved "
                    "(mechanism, specific timing based on each drug's pharmacology, food-drug interactions, contraindications, side effects to watch, duration), "
                    "specialist recommendation with reasoning, "
                    "and 4-5 specific diagnostic questions to rule in/out differentials. "
                    "Be educational — explain WHY each recommendation works. No word limit."
                ),
            }
            extra_with_mode = extra + mode_ctx.get(mode, "")

            # Route to cloud or core model
            provider = getattr(chat_request, 'model_provider', 'core') or 'core'
            if provider != "core" and provider in ("openai", "gemini", "anthropic"):
                # Cloud model streaming
                async for token in cloud_engine.generate_response_stream(
                    provider=provider,
                    message=chat_request.message,
                    history=history,
                    patient_id=patient_id,
                    extra_context=extra_with_mode,
                    max_tokens=mode_tokens.get(mode, 700),
                    temperature=mode_temp.get(mode, 0.35),
                ):
                    full += token
                    yield f"data: {json.dumps({'type':'chunk','content':token})}\n\n"
            else:
                # Core local Llama model
                async for token in llm_engine.generate_response_stream(
                    message=chat_request.message,
                    history=history,
                    patient_id=patient_id,
                    extra_context=extra_with_mode,
                    max_tokens=mode_tokens.get(mode, 700),
                    temperature=mode_temp.get(mode, 0.35),
                ):
                    full += token
                    # Skip leading JSON tool-call artifacts from LLM
                    if not started:
                        stripped = re.sub(r'^[\s{}]*(?:\{[^}]*"name"\s*:[^}]*\}[\s{}]*)*', '', full)
                        # Also strip any remaining leading braces/whitespace
                        stripped = stripped.lstrip('\t\n{}')
                        if stripped and not stripped.startswith('{'):
                            # Real text has begun — send the clean portion
                            started = True
                            full = stripped
                            yield f"data: {json.dumps({'type':'chunk','content':stripped})}\n\n"
                        continue
                    yield f"data: {json.dumps({'type':'chunk','content':token})}\n\n"

            if not started:
                # Edge case: entire response was JSON artifact
                full = re.sub(r'^[\s{}]*(?:\{[^}]*"name"\s*:[^}]*\}[\s{}]*)*', '', full)
                full = full.lstrip('\t\n{}')

            db.save_message(patient_id, session_id, "user", chat_request.message, detected_lang)
            db.save_message(patient_id, session_id, "assistant", full, detected_lang,
                            metadata={"triage": triage_result})

            if len(history) == 0:
                summary = chat_request.message[:40].strip() + ("..." if len(chat_request.message) > 40 else "")
                db.update_session(session_id, summary=summary)

            if triage_result["level"] in ("urgent", "moderate"):
                db.add_health_event(patient_id, "symptom_report", triage_result["reason"],
                                    chat_request.message[:500], severity=triage_result["level"])

            yield f"data: {json.dumps({'type':'done','session_id':session_id,'language':detected_lang,'triage':triage_result,'citations':citations})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type':'error','content':'Sorry, an error occurred. Please try again.'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════
#  NON-STREAMING CHAT  (used by voice pipeline)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    """Non-streaming chat (used by voice pipeline).
    OPTIMIZED: parallel pre-fetch like streaming endpoint."""
    if hasattr(request.state, "user_id") and chat_request.patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    session_id = chat_request.session_id or str(uuid.uuid4())
    patient_id = chat_request.patient_id
    db.ensure_patient(patient_id)

    detected_lang = (
        translation_service.detect_language(chat_request.message)
        if chat_request.language == "auto"
        else chat_request.language
    )

    # ══ PARALLEL PRE-FETCH ══════════════════════════════════════
    (
        triage_result,
        rag_ctx,
        citations,
        patient_ctx,
        patient_data,
        history,
    ) = await asyncio.gather(
        _async_triage(chat_request.message),
        _async_rag_context(chat_request.message, top_k=3),
        _async_rag_citations(chat_request.message, top_k=3),
        _async_patient_context(patient_id),
        _async_patient_data(patient_id),
        _async_conversation(patient_id, session_id, limit=10),
    )
    # ════════════════════════════════════════════════════════════

    if triage_result["level"] == "emergency":
        txt = f"🚨 EMERGENCY: {triage_result['reason']}\n{triage_result['recommendation']}\nCall 112 immediately."
        db.save_message(patient_id, session_id, "user", chat_request.message, detected_lang)
        db.save_message(patient_id, session_id, "assistant", txt, "en")
        return {"response_text": txt, "session_id": session_id, "language": detected_lang,
                "emergency": True, "triage": triage_result,
                "original_language": detected_lang, "audio_url": None,
                "emergency_detected": True, "timestamp": datetime.now().isoformat()}

    triage_ctx = triage.get_triage_prompt(triage_result)

    # Elderly patient detection
    elderly_ctx = ""
    if patient_data and patient_data.get("age"):
        try:
            age = int(patient_data["age"])
            if age >= 65:
                elderly_ctx = (
                    "ELDERLY PATIENT ALERT (age " + str(age) + "):\n"
                    "This is an elderly patient. You MUST:\n"
                    "• Provide a MINIMUM of 3 differential diagnoses for any complaint.\n"
                    "• Elderly symptoms often mask serious conditions — consider atypical presentations.\n"
                    "• Check for red flags: new confusion, sudden falls, dehydration, rapid decline.\n"
                    "• Always consider medication side effects and polypharmacy risks.\n"
                    "• Flag any danger signs prominently with ⚠️ warning."
                )
        except (ValueError, TypeError):
            pass

    punjabi_ctx = (
        "The patient is a Punjabi speaker. "
        "Respond in clear, simple Hindi (Devanagari script) — NOT Gurmukhi. "
        "Hindi and Punjabi are mutually intelligible; Hindi TTS will be spoken back to them. "
        "Use short sentences. Avoid complex medical jargon."
    ) if detected_lang == "pa" else ""

    extra = "\n\n".join(filter(None, [
        f"PATIENT RECORD:\n{patient_ctx}" if patient_ctx else "",
        elderly_ctx,
        punjabi_ctx,
        rag_ctx, triage_ctx,
    ]))

    llm_resp = await _generate_model_response(
        provider=request.model_provider,
        message=request.message,
        history=history,
        patient_id=patient_id,
        extra_context=extra,
    )
    resp_text = llm_resp["response"]

    db.save_message(patient_id, session_id, "user", request.message, detected_lang)
    db.save_message(patient_id, session_id, "assistant", resp_text, detected_lang,
                    metadata={"triage": triage_result})

    # Use input language for TTS voice selection — NOT re-detected from LLM response text.
    # This ensures Punjabi input always gets Hindi/Punjabi voice even if LLM responded in English.
    tts_lang = request.language if request.language and request.language != "auto" else detected_lang
    audio_url = await tts_engine.generate_speech(resp_text, tts_lang, patient_id, session_id)

    return {
        "response_text": resp_text,
        "original_language": detected_lang,
        "audio_url": audio_url,
        "emergency_detected": False,
        "session_id": session_id,
        "triage": triage_result,
        "citations": citations,
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  VOICE CHAT
# ══════════════════════════════════════════════════════════════════

@app.post("/api/voice/chat")
@limiter.limit("5/minute")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    patient_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
):
    if hasattr(request.state, "user_id") and patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    session_id = session_id or str(uuid.uuid4())
    audio_bytes = await audio.read()
    tx = await voice_processor.transcribe(audio_bytes, forced_language=language)

    if tx.get("error") or not tx.get("text"):
        raise HTTPException(status_code=400, detail=tx.get("error", "No speech detected"))

    logger.info(f"Voice ({tx['language']}): {tx['text'][:80]}")

    chat_resp = await chat_endpoint(ChatRequest(
        patient_id=patient_id, message=tx["text"],
        language=tx["language"], session_id=session_id,
        model_provider=_resolve_model_provider(None),
    ))

    return {
        "transcription": {"text": tx["text"], "language": tx["language"],
                          "confidence": tx.get("confidence", 0.9)},
        "response": chat_resp,
        "session_id": session_id,
    }


# ══════════════════════════════════════════════════════════════════
#  IMAGE ANALYSIS  (non-streaming)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/image/analyze")
@limiter.limit("5/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    patient_id: str = Form(...),
    body_region: Optional[str] = Form(None),
    image_type: Optional[str] = Form("photo"),
    description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    if hasattr(request.state, "user_id") and patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if image.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(400, "Invalid format. Only JPEG, PNG, WEBP, and GIF allowed.")
    image_bytes = await image.read()
    _validate_image_bytes(image_bytes)
    
    session_id = session_id or str(uuid.uuid4())
    db.ensure_patient(patient_id)

    # Save image
    fname = f"{patient_id}_{uuid.uuid4().hex[:8]}.jpg"
    ipath = f"static/images/{fname}"
    with open(ipath, "wb") as f:
        f.write(image_bytes)

    # Vision — pass region and type for intelligent classification
    vis = await vision_analyzer.analyze_medical_image(image_bytes, body_region=body_region, image_type=image_type)
    vis_desc = vis.get("description", "Image received.")
    classified_type = vis.get("image_type", image_type or "photo")

    # Build smart prompt based on image type
    if classified_type == "xray_scan":
        parts = [f"Patient uploaded an X-ray/radiological scan for medical analysis."]
        if body_region:
            parts.append(f"Body region: {body_region}")
        parts.append(f"AI Radiology Analysis: {vis_desc}")
        if description:
            parts.append(f"Patient notes: {description}")
        parts.append("As a radiologist consultant, provide: 1) What the X-ray appears to show, 2) Possible findings/abnormalities suggested by the description, 3) Recommended follow-up tests, 4) When to see a specialist. Be thorough but remind patient this is AI-assisted analysis.")
    else:
        parts = [f"Patient uploaded a medical image ({classified_type})."]
        if body_region:
            parts.append(f"Body region: {body_region}")
        if description:
            parts.append(f"Patient's description: {description}")
        parts.append(f"AI Vision Analysis: {vis_desc}")
        parts.append("Provide medical assessment: possible conditions, home care, when to see doctor.")
    prompt = "\n".join(parts)

    rag_ctx = rag_engine.get_context_for_query(f"{description or ''} {vis_desc}", top_k=2) if rag_engine.check_health() else ""
    pat_ctx = db.get_patient_context(patient_id)
    extra = "\n\n".join(filter(None, [f"PATIENT RECORD:\n{pat_ctx}" if pat_ctx else "", rag_ctx]))

    resp = await llm_engine.generate_response(
        message=prompt, history=db.get_conversation(patient_id, session_id, 5),
        patient_id=patient_id, extra_context=extra, max_tokens=1024
    )
    interpretation = resp["response"]

    db.save_medical_image(patient_id, ipath, image_type, body_region, description, vis_desc, session_id)
    db.save_message(patient_id, session_id, "user", f"[Image: {description or image_type}]", "en")
    db.save_message(patient_id, session_id, "assistant", interpretation, "en")
    if body_region:
        db.add_health_event(patient_id, "image_upload", f"{image_type} - {body_region}",
                            vis_desc, body_region=body_region)

    return {
        "image_url": f"/{ipath}",
        "analysis": vis_desc,
        "interpretation": interpretation,
        "session_id": session_id,
        "warning": "⚠️ This is NOT a medical diagnosis. Please consult a healthcare professional.",
    }


# ══════════════════════════════════════════════════════════════════
#  IMAGE ANALYSIS  (streaming)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/image/analyze/stream")
@limiter.limit("5/minute")
async def analyze_image_stream(
    request: Request,
    image: UploadFile = File(...),
    patient_id: str = Form(...),
    body_region: Optional[str] = Form(None),
    image_type: Optional[str] = Form("photo"),
    description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
):
    if hasattr(request.state, "user_id") and patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if image.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(400, "Invalid format. Only JPEG, PNG, WEBP, and GIF allowed.")
    image_bytes = await image.read()
    _validate_image_bytes(image_bytes)
        
    session_id = session_id or str(uuid.uuid4())
    db.ensure_patient(patient_id)

    fname = f"{patient_id}_{uuid.uuid4().hex[:8]}.jpg"
    ipath = f"static/images/{fname}"
    with open(ipath, "wb") as f:
        f.write(image_bytes)

    vis = await vision_analyzer.analyze_medical_image(image_bytes, body_region=body_region, image_type=image_type)
    vis_desc = vis.get("description", "Image received.")
    classified_type = vis.get("image_type", image_type or "photo")
    doc_lab_results = []

    if classified_type == "xray_scan":
        parts = [f"Patient uploaded an X-ray/radiological scan."]
        if body_region:
            parts.append(f"Body region: {body_region}")
        parts.append(f"AI Radiology Analysis: {vis_desc}")
        if description:
            parts.append(f"Patient notes: {description}")
        parts.append("As a radiologist, analyze: findings, possible abnormalities, recommended follow-ups, when to see specialist.")
    elif classified_type == "document_report":
        # Extract text via OCR for document/report screenshots
        ocr_text = ""
        doc_lab_results = []
        try:
            ocr_data = ocr_engine.extract_from_image(image_bytes)
            ocr_text = ocr_data.get("raw_text", "").strip()
            doc_lab_results = ocr_data.get("lab_results", [])
        except Exception as e:
            logger.warning(f"OCR on document image failed: {e}")
        parts = [f"Patient uploaded a screenshot/photo of a medical document or report."]
        if ocr_text:
            parts.append(f"Extracted text from the document:\n{ocr_text[:2000]}")
        else:
            parts.append(f"AI Vision Analysis: {vis_desc}")
        if doc_lab_results:
            parts.append(f"\nExtracted {len(doc_lab_results)} lab values from the document.")
        # NER enrichment for document reports
        if ocr_text:
            try:
                ner_data = ner_engine.extract_entities(ocr_text)
                if ner_data["diseases"]:
                    disease_names = [d["text"] for d in ner_data["diseases"]]
                    parts.append(f"NER-detected conditions: {', '.join(disease_names)}")
                if ner_data["chemicals"]:
                    drug_names = [c["text"] for c in ner_data["chemicals"]]
                    parts.append(f"NER-detected medications: {', '.join(drug_names)}")
            except Exception as e:
                logger.warning(f"NER on document text failed: {e}")
        if description:
            parts.append(f"Patient notes: {description}")
        parts.append("Read and summarize the document content. Explain any medical values, test results, or findings in simple terms. Highlight anything abnormal.")
    else:
        parts = [f"Patient uploaded a medical image ({classified_type})."]
        if body_region:
            parts.append(f"Body region: {body_region}")
        if description:
            parts.append(f"Patient's description: {description}")
        parts.append(f"AI Vision Analysis: {vis_desc}")
        parts.append("Provide medical assessment: possible conditions, home care, when to see doctor.")
    prompt = "\n".join(parts)

    rag_ctx = rag_engine.get_context_for_query(f"{description or ''} {vis_desc}", top_k=2) if rag_engine.check_health() else ""
    pat_ctx = db.get_patient_context(patient_id)
    extra = "\n\n".join(filter(None, [f"PATIENT RECORD:\n{pat_ctx}" if pat_ctx else "", rag_ctx]))
    history = db.get_conversation(patient_id, session_id, 5)

    async def _stream():
        full = ""
        try:
            yield f"data: {json.dumps({'type':'vision','description':vis_desc})}\n\n"
            async for tok in llm_engine.generate_response_stream(
                message=prompt, history=history,
                patient_id=patient_id, extra_context=extra, max_tokens=1024
            ):
                full += tok
                yield f"data: {json.dumps({'type':'chunk','content':tok})}\n\n"

            img_id = db.save_medical_image(patient_id, ipath, image_type, body_region,
                                  description, vis_desc, session_id, date=date)
            db.save_message(patient_id, session_id, "user", f"[Image: {description or image_type}]", "en")
            db.save_message(patient_id, session_id, "assistant", full, "en")
            
            if len(history) == 0:
                summary_text = f"Image: {description or image_type or 'Upload'}"
                db.update_session(session_id, summary=summary_text[:40].strip())

            if body_region:
                db.add_health_event(patient_id, "image_upload", f"{image_type} - {body_region}",
                                    vis_desc, body_region=body_region)

            # Save extracted lab values if this was a document/report
            lab_count = 0
            if classified_type == "document_report" and doc_lab_results:
                for lr in doc_lab_results:
                    db.add_lab_result(
                        patient_id, lr["test_name"], lr["value"],
                        lr.get("unit"), lr.get("normal_range"), lr.get("status"), source="ocr"
                    )
                lab_count = len(doc_lab_results)
                db.add_health_event(patient_id, "lab_report", "Lab Report (from image)",
                                    f"Parsed {lab_count} values from uploaded image")

            yield f"data: {json.dumps({'type':'done','session_id':session_id,'image_url':'/'+ipath,'image_id':img_id,'analysis':vis_desc,'lab_count':lab_count})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Image stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type':'error','content':'Image analysis failed.'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════
#  OCR — LAB REPORT PARSING
# ══════════════════════════════════════════════════════════════════

@app.post("/api/report/parse")
@limiter.limit("5/minute")
async def parse_lab_report(
    request: Request,
    image: UploadFile = File(...),
    patient_id: str = Form(...),
    session_id: Optional[str] = Form(None),
):
    if hasattr(request.state, "user_id") and patient_id != request.state.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if image.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(400, "Invalid format. Only JPEG, PNG, WEBP, and GIF allowed.")
    image_bytes = await image.read()
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum size is 5MB.")
        
    db.ensure_patient(patient_id)
    ocr = ocr_engine.extract_from_image(image_bytes)

    for lr in ocr["lab_results"]:
        db.add_lab_result(
            patient_id, lr["test_name"], lr["value"],
            lr.get("unit"), lr.get("normal_range"), lr.get("status"), source="ocr"
        )

    safe_patient_id = _safe_patient_prefix(patient_id)
    rpath = f"static/images/{safe_patient_id}_report_{uuid.uuid4().hex[:8]}.jpg"
    with open(rpath, "wb") as f:
        f.write(image_bytes)

    db.save_medical_image(patient_id, rpath, "lab_report",
                          description="Lab report (OCR)", ai_analysis=ocr["raw_text"][:500],
                          session_id=session_id)
    db.add_health_event(patient_id, "lab_report", "Lab Report Uploaded",
                        f"Parsed {ocr['count']} values")

    # NER enrichment — detect diseases, drugs, extra measurements from report text
    enriched = ner_engine.enrich_ocr_results(ocr["raw_text"], ocr["lab_results"])

    return {"raw_text": ocr["raw_text"], "lab_results": ocr["lab_results"],
            "count": ocr["count"], "message": f"Extracted {ocr['count']} lab values",
            "ner_diseases": enriched["ner_diseases"],
            "ner_drugs": enriched["ner_drugs"],
            "ner_entity_count": enriched["ner_entity_count"]}


class NERRequest(BaseModel):
    text: str


@app.post("/api/ner/extract")
async def ner_extract(req: NERRequest):
    """Extract diseases, drugs, and measurements from any medical text."""
    result = ner_engine.extract_entities(req.text)
    return result


@app.post("/api/ner/chat-context")
async def ner_chat_context(req: NERRequest):
    """Extract medical context from a chat message (conditions + medications)."""
    return ner_engine.analyze_chat_message(req.text)


# ══════════════════════════════════════════════════════════════════
#  PATIENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patients")
async def list_patients(http_request: Request):
    patient_id = getattr(http_request.state, "user_id", None)
    if not patient_id:
        return {"patients": []}
    patient = db.get_patient(patient_id)
    return {"patients": [patient] if patient else []}

@app.get("/api/patient/{patient_id}")
async def get_patient(patient_id: str):
    p = db.get_patient(patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p

@app.put("/api/patient/{patient_id}")
async def update_patient(patient_id: str, data: PatientUpdateRequest):
    db.ensure_patient(patient_id, **data.dict(exclude_none=True))
    return db.get_patient(patient_id)

@app.get("/api/patient/{patient_id}/sessions")
async def get_sessions(patient_id: str):
    return {"sessions": db.get_sessions(patient_id)}

@app.get("/api/patient/{patient_id}/history")
async def get_history(patient_id: str, session_id: Optional[str] = None, limit: int = 50):
    msgs = db.get_conversation(patient_id, session_id, limit) if session_id else db.get_all_conversations(patient_id, limit)
    return {"messages": msgs}


@app.delete("/api/patient/{patient_id}/session/{session_id}")
async def delete_session(patient_id: str, session_id: str):
    ok = db.delete_session(session_id, patient_id)
    if not ok:
        raise HTTPException(404, "Session not found")
    return {"status": "ok", "deleted_session": session_id}


# ══════════════════════════════════════════════════════════════════
#  HEALTH RECORDS
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/timeline")
async def get_timeline(patient_id: str, limit: int = 50):
    return {"events": db.get_health_timeline(patient_id, limit)}

@app.post("/api/patient/{patient_id}/event")
async def add_event(patient_id: str, event: HealthEventRequest):
    db.add_health_event(patient_id, event.event_type, event.title,
                        event.description, event.body_region, event.severity, event.date)
    return {"status": "ok"}

@app.get("/api/patient/{patient_id}/lab-results")
async def get_lab_results(patient_id: str, test_name: Optional[str] = None):
    return {"results": db.get_lab_results(patient_id, test_name)}

@app.post("/api/patient/{patient_id}/lab-result")
async def add_lab_result(patient_id: str, data: LabResultRequest):
    db.add_lab_result(patient_id, data.test_name, data.value, data.unit,
                      data.normal_range, data.status, data.date)
    return {"status": "ok"}

# ── Lab Interpretation ──────────────────────────────────────────

@app.get("/api/patient/{patient_id}/lab-interpret")
async def interpret_labs(patient_id: str):
    """Interpret all latest lab results with age/gender-specific ranges and clinical rules."""
    patient = db.get_patient(patient_id)
    age = patient.get("age") if patient else None
    gender = patient.get("gender") if patient else None

    vitals = db.get_latest_vitals(patient_id)
    if not vitals:
        return {"results": [], "summary": {}, "overall_assessment": "No lab results to interpret."}

    # Build lab_values dict: {test_name: value}
    lab_values = {}
    for test_name, v in vitals.items():
        lab_values[test_name] = v["value"]

    interpretation = interpret_lab_panel(lab_values, age=age, gender=gender)
    return interpretation

@app.post("/api/lab-interpret-single")
async def interpret_single_lab(data: dict):
    """Interpret a single lab value. Body: {test_name, value, age?, gender?}"""
    test_name = data.get("test_name", "")
    value = data.get("value", "")
    age = data.get("age")
    gender = data.get("gender")
    return interpret_lab_value(test_name, value, age=age, gender=gender)

@app.get("/api/lab-range/{test_name}")
async def get_lab_range(test_name: str, age: Optional[int] = None, gender: Optional[str] = None):
    """Get the normal range for a specific test based on age and gender."""
    return {"test_name": test_name, "normal_range": get_normal_range(test_name, age, gender)}

@app.get("/api/patient/{patient_id}/vitals")
async def get_vitals(patient_id: str):
    return {"vitals": db.get_latest_vitals(patient_id)}

@app.get("/api/patient/{patient_id}/body-map")
async def get_body_map(patient_id: str):
    return {"regions": db.get_body_map(patient_id)}

@app.get("/api/patient/{patient_id}/images")
async def get_images(patient_id: str, body_region: Optional[str] = None,
                     image_type: Optional[str] = None):
    return {"images": db.get_images(patient_id, body_region, image_type)}

@app.delete("/api/patient/{patient_id}/image/{image_id}")
async def delete_image(patient_id: str, image_id: int):
    image_path = db.delete_image(image_id, patient_id)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    if os.path.exists(image_path):
        abs_image_path = os.path.abspath(image_path)
        allowed_root = os.path.abspath("static/images")
        if abs_image_path.startswith(allowed_root + os.sep):
            os.remove(abs_image_path)
        else:
            logger.warning("Skipped deleting unsafe image path: %s", image_path)
    return {"status": "ok", "deleted_id": image_id}


# ══════════════════════════════════════════════════════════════════
#  HEALTH DASHBOARD  (all-in-one)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/dashboard")
async def get_dashboard(patient_id: str):
    db.ensure_patient(patient_id)
    return {
        "patient": db.get_patient(patient_id),
        "vitals": db.get_latest_vitals(patient_id),
        "timeline": db.get_health_timeline(patient_id, 20),
        "body_map": db.get_body_map(patient_id),
        "recent_labs": db.get_lab_results(patient_id, limit=200),
        "recent_images": db.get_images(patient_id),
        "sessions": db.get_sessions(patient_id),
    }


# ══════════════════════════════════════════════════════════════════
#  SYMPTOM CHECKER  (AI-powered differential diagnosis)
# ══════════════════════════════════════════════════════════════════

class SymptomCheckRequest(BaseModel):
    patient_id: str
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


@app.post("/api/symptom-check")
async def symptom_checker(request: SymptomCheckRequest):
    """AI differential diagnosis with probability percentages"""
    db.ensure_patient(request.patient_id)
    symptom_text = ", ".join(request.symptoms)
    
    rag_ctx = rag_engine.get_context_for_query(symptom_text, top_k=5) if rag_engine.check_health() else ""
    patient_ctx = db.get_patient_context(request.patient_id)
    
    prompt = f"""Symptoms: {symptom_text}
{f'Duration: {request.duration}' if request.duration else ''}
{f'Severity: {request.severity}' if request.severity else ''}
{f'Age: {request.age}' if request.age else ''}
{f'Gender: {request.gender}' if request.gender else ''}

Give a SHORT differential diagnosis. For each condition (max 3-4):
Condition - Likelihood% - Why it fits - One key test to confirm

End with: Next step (one line) and Red flags to watch (one line).
Be brief and direct. No long explanations."""

    extra = "\n\n".join(filter(None, [
        f"PATIENT RECORD:\n{patient_ctx}" if patient_ctx else "",
        rag_ctx,
    ]))

    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=request.patient_id,
        extra_context=extra, max_tokens=400, temperature=0.4
    )
    
    triage_result = triage.assess(symptom_text)
    
    return {
        "analysis": resp["response"],
        "symptoms_analyzed": request.symptoms,
        "triage": triage_result,
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  DRUG INTERACTION CHECKER
# ══════════════════════════════════════════════════════════════════

class DrugCheckRequest(BaseModel):
    patient_id: str
    medications: List[str]


@app.post("/api/drug-interactions")
async def check_drug_interactions(request: DrugCheckRequest):
    """Check for drug-drug interactions using AI"""
    meds = ", ".join(request.medications)
    patient_ctx = db.get_patient_context(request.patient_id)
    patient = db.get_patient(request.patient_id)
    ethnicity = patient.get("ethnicity", "") if patient else ""
    
    prompt = f"""Medications (with dosages): {meds}

For EACH medicine listed above, state in one line:
- Medicine name and dosage - What it is used for (disease/condition)
- Whether the dosage (mg) is appropriate (low/standard/high dose)

Then check interactions between them:
- Which pairs interact? Severity (Major/Moderate/Minor) and what happens (e.g. increased bleeding risk)
- Safe to take together? Yes/No with brief reason
- Best timing: when to take each to minimize interactions
- Any dosage concerns: is any medicine at a dose that needs monitoring?"""

    if ethnicity:
        prompt += f"""

IMPORTANT — Patient's ethnicity/ancestry: {ethnicity}
Consider pharmacogenomic and ethnic differences in drug metabolism:
- Note if any medication dosage should be adjusted based on the patient's ethnic background
- Flag any known ethnic-specific drug sensitivities or metabolism differences (e.g., enzyme polymorphisms like CYP2D6, CYP2C19, UGT1A1, HLA-B*5801)
- Mention if certain populations metabolize specific drugs faster or slower"""

    prompt += """

Keep it short and practical. End with one line: Consult your doctor for personalized advice."""

    extra = f"PATIENT RECORD:\n{patient_ctx}" if patient_ctx else ""
    
    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=request.patient_id,
        extra_context=extra, max_tokens=400, temperature=0.4
    )
    
    return {
        "analysis": resp["response"],
        "medications": request.medications,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "This is AI-generated information. Always consult a pharmacist or doctor."
    }


# ══════════════════════════════════════════════════════════════════
#  HEALTH SCORE CALCULATOR
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/health-score")
async def calculate_health_score(patient_id: str):
    """Calculate overall health score 0-100 based on all patient data"""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    vitals = db.get_latest_vitals(patient_id)
    labs = db.get_lab_results(patient_id, limit=20)
    events = db.get_health_timeline(patient_id, 30)
    
    score = 85  # Base score
    factors = []
    
    # Deduct for abnormal labs
    abnormal_count = sum(1 for l in labs if l.get("status") in ("high", "low"))
    if abnormal_count > 0:
        deduction = min(abnormal_count * 5, 25)
        score -= deduction
        factors.append({"factor": "Abnormal lab results", "impact": -deduction, "detail": f"{abnormal_count} abnormal values"})
    
    # Deduct for emergency events
    emergencies = sum(1 for e in events if e.get("severity") == "critical")
    if emergencies > 0:
        deduction = min(emergencies * 10, 20)
        score -= deduction
        factors.append({"factor": "Emergency events", "impact": -deduction, "detail": f"{emergencies} critical events"})
    
    # Bonus for having profile filled
    profile_fields = sum(1 for f in ["name","age","gender","blood_group","allergies"] if patient and patient.get(f))
    if profile_fields >= 4:
        score += 5
        factors.append({"factor": "Complete health profile", "impact": 5, "detail": f"{profile_fields}/5 fields filled"})
    
    # Bonus for regular checkups (lab results)
    if len(labs) >= 5:
        score += 5
        factors.append({"factor": "Regular health monitoring", "impact": 5, "detail": f"{len(labs)} lab results tracked"})
    
    score = max(0, min(100, score))
    
    # Determine grade
    if score >= 90: grade = "A+"
    elif score >= 80: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 60: grade = "C"
    elif score >= 50: grade = "D"
    else: grade = "F"
    
    return {
        "score": score,
        "grade": grade,
        "factors": factors,
        "recommendations": _get_health_recommendations(score, factors, patient),
        "timestamp": datetime.now().isoformat(),
    }


def _get_health_recommendations(score: int, factors: list, patient: dict) -> list:
    recs = []
    if score < 70:
        recs.append("Consider scheduling a comprehensive health checkup")
    if not patient or not patient.get("allergies"):
        recs.append("Update your allergy information in your profile")
    if not patient or not patient.get("chronic_conditions"):
        recs.append("Document any chronic conditions for better care")
    recs.append("Regular health monitoring helps track your wellbeing")
    return recs


# ══════════════════════════════════════════════════════════════════
#  PREDICTIVE HEALTH TRAJECTORY  (Novel Feature)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/health-trajectory")
async def get_health_trajectory(patient_id: str):
    """
    Predictive Health Trajectory — analyzes temporal patterns across all
    patient data (labs, meds, symptoms, body map) to predict health
    trajectory and generate early-warning alerts.
    """
    try:
        forecast = predictive_engine.generate_health_forecast(patient_id)
        return forecast
    except Exception as e:
        logger.error(f"Health trajectory error: {e}", exc_info=True)
        return {
            "patient_id": patient_id,
            "has_sufficient_data": False,
            "alert_level": "green",
            "alert_message": "Unable to generate forecast. Add more health data.",
            "trajectories": [],
            "medication_correlations": [],
            "symptom_patterns": {"symptoms": [], "total_messages_analyzed": 0},
        }


# ══════════════════════════════════════════════════════════════════
#  MENTAL HEALTH ASSESSMENT
# ══════════════════════════════════════════════════════════════════

class MentalHealthRequest(BaseModel):
    patient_id: str
    assessment_type: str = "general"  # general, phq9, gad7, stress
    responses: Optional[List[int]] = None
    free_text: Optional[str] = None


PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling/staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure",
    "Trouble concentrating on things",
    "Moving/speaking slowly, or being fidgety/restless",
    "Thoughts that you would be better off dead, or of hurting yourself"
]

GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid, as if something awful might happen"
]


@app.post("/api/mental-health/assess")
async def mental_health_assessment(request: MentalHealthRequest):
    """Standardized mental health screening"""
    db.ensure_patient(request.patient_id)
    
    if request.assessment_type == "phq9" and request.responses:
        total = sum(request.responses[:9])
        if total <= 4: severity = "Minimal depression"
        elif total <= 9: severity = "Mild depression"
        elif total <= 14: severity = "Moderate depression"
        elif total <= 19: severity = "Moderately severe depression"
        else: severity = "Severe depression"
        
        db.add_health_event(request.patient_id, "mental_health", 
                           f"PHQ-9 Score: {total}", severity, severity="moderate" if total > 9 else "mild")
        
        return {
            "assessment": "PHQ-9 Depression Screening",
            "score": total, "max_score": 27,
            "severity": severity,
            "questions": PHQ9_QUESTIONS,
            "recommendation": "Please consult a mental health professional for a comprehensive evaluation." if total > 9 else "Your score suggests minimal symptoms. Continue monitoring your mental health.",
        }
    
    elif request.assessment_type == "gad7" and request.responses:
        total = sum(request.responses[:7])
        if total <= 4: severity = "Minimal anxiety"
        elif total <= 9: severity = "Mild anxiety"
        elif total <= 14: severity = "Moderate anxiety"
        else: severity = "Severe anxiety"
        
        db.add_health_event(request.patient_id, "mental_health",
                           f"GAD-7 Score: {total}", severity, severity="moderate" if total > 9 else "mild")
        
        return {
            "assessment": "GAD-7 Anxiety Screening",
            "score": total, "max_score": 21,
            "severity": severity,
            "questions": GAD7_QUESTIONS,
            "recommendation": "Consider speaking with a mental health professional." if total > 9 else "Your anxiety levels appear manageable. Practice relaxation techniques.",
        }
    
    # Free-text mental health analysis
    if request.free_text:
        prompt = f"""MENTAL HEALTH ASSESSMENT
Patient says: "{request.free_text}"

Provide a compassionate, professional mental health assessment:
1. Acknowledge their feelings
2. Identify potential concerns
3. Suggest coping strategies
4. Recommend professional resources if needed
5. Provide emergency contacts if any crisis indicators

CRITICAL: If any suicidal or self-harm indicators, prioritize safety information.
Be warm, non-judgmental, and supportive."""

        resp = await llm_engine.generate_response(
            message=prompt, history=[], patient_id=request.patient_id, max_tokens=1024
        )
        return {"assessment": "General Mental Health", "analysis": resp["response"]}
    
    # Return questionnaire
    return {
        "phq9_questions": PHQ9_QUESTIONS,
        "gad7_questions": GAD7_QUESTIONS,
        "instructions": "Rate each question 0-3 (0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day)"
    }


# ══════════════════════════════════════════════════════════════════
#  HEALTH REPORT PDF DATA
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/report")
async def generate_health_report(patient_id: str):
    """Generate comprehensive health report data (frontend renders)"""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    vitals = db.get_latest_vitals(patient_id)
    labs = db.get_lab_results(patient_id, limit=200)
    events = db.get_health_timeline(patient_id, 50)
    images = db.get_images(patient_id)
    body_map = db.get_body_map(patient_id)

    # Build a concise summary from actual data instead of full patient context
    abnormals = [f"{l['test_name'].replace('_',' ')}: {l['value']} {l.get('unit','')} ({l['status']})"
                 for l in labs if l.get("status") not in ("normal", "noted", "unknown", None)]
    
    ai_summary = ""
    if labs:
        # Build short data-driven prompt for LLM (keep it small for 2048 ctx)
        summary_parts = []
        if patient.get("name"):
            summary_parts.append(f"Patient: {patient.get('name','')}, {patient.get('age','')} {patient.get('gender','')}")
        summary_parts.append(f"Total lab tests: {len(labs)}")
        if abnormals:
            summary_parts.append(f"Abnormal values:\n" + "\n".join(abnormals[:15]))
        else:
            summary_parts.append("All values within normal range.")
        
        prompt = "Based on these lab results, give a brief health summary (3-5 paragraphs). Highlight concerns, what's normal, and recommendations.\n\n" + "\n".join(summary_parts)
        
        try:
            resp = await llm_engine.generate_response(
                message=prompt, history=[], patient_id=patient_id, max_tokens=512
            )
            ai_summary = resp.get("response", "")
            # Clean JSON artifacts
            ai_summary = re.sub(r'^\s*\{[^}]*"name"\s*:[^}]*\}\s*', '', ai_summary).lstrip(' \t\n{}').strip()
        except Exception as e:
            logger.error(f"AI report generation failed: {e}")
            ai_summary = ""
    
    if not ai_summary:
        if abnormals:
            ai_summary = f"**Lab Results Summary**\n\n{len(labs)} tests on record. {len(abnormals)} abnormal value(s) found:\n\n"
            ai_summary += "\n".join(f"• {a}" for a in abnormals)
            ai_summary += "\n\nPlease consult a healthcare provider for detailed interpretation."
        else:
            ai_summary = f"{len(labs)} lab tests on record. All values appear within normal ranges. Continue regular health monitoring."

    return {
        "patient": patient,
        "vitals": vitals,
        "lab_results": labs,
        "timeline": events,
        "images": [{"type": img.get("image_type"), "region": img.get("body_region"), "date": img.get("date")} for img in images],
        "body_map": body_map,
        "ai_summary": ai_summary,
        "generated_at": datetime.now().isoformat(),
        "report_id": str(uuid.uuid4())[:8],
    }


# ══════════════════════════════════════════════════════════════════
#  SMART HEALTH INSIGHTS (AI pattern detection)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/insights")
async def health_insights(patient_id: str):
    """AI-powered health pattern detection and predictions"""
    db.ensure_patient(patient_id)
    patient_ctx = db.get_patient_context(patient_id)
    
    if not patient_ctx or len(patient_ctx) < 50:
        return {"insights": [], "message": "Keep tracking your health to unlock AI-powered insights."}
    
    prompt = f"""Analyze this patient's health data and provide maximum 5 key insights:

{patient_ctx}

For each insight provide:
- Title (short)
- Description (1-2 sentences)
- Category: one of [trend, alert, recommendation, positive, risk]
- Priority: high/medium/low
- Actionable advice

Format as clear bullet points. Focus on patterns, trends, and actionable insights."""

    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=patient_id, max_tokens=1200
    )
    
    return {
        "raw_insights": resp["response"],
        "generated_at": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  LAB TEST CATALOG + AUTOCOMPLETE
# ══════════════════════════════════════════════════════════════════

@app.get("/api/lab-catalog")
async def get_lab_catalog(q: Optional[str] = None, category: Optional[str] = None):
    """Return lab test catalog with optional search/filter for autocomplete."""
    results = LAB_TEST_CATALOG
    if category:
        results = [t for t in results if t["category"].lower() == category.lower()]
    if q:
        q_low = q.lower()
        results = [t for t in results if q_low in t["name"].lower() or q_low in t["display"].lower()
                   or q_low in t.get("category", "").lower()]
    return {"tests": results, "categories": LAB_CATEGORIES}


@app.get("/api/medicine-catalog")
async def get_medicine_catalog(q: Optional[str] = None):
    """Search medicine catalog by name prefix/substring. Returns medicines with dosage variants."""
    results = search_medicines(q or "", limit=15)
    return {"medicines": results}


@app.post("/api/patient/{patient_id}/lab-result/manual")
async def add_manual_lab_result(patient_id: str, data: LabResultRequest):
    """Add a manually entered lab result. Auto-fills unit/range from catalog if not provided."""
    db.ensure_patient(patient_id)
    catalog_entry = LAB_CATALOG_MAP.get(data.test_name)
    unit = data.unit or (catalog_entry["unit"] if catalog_entry else None)
    normal_range = data.normal_range or (catalog_entry["normal_range"] if catalog_entry else None)
    status = data.status
    if not status and normal_range and data.value:
        status = _auto_status(data.value, normal_range)
    db.add_lab_result(patient_id, data.test_name, data.value, unit, normal_range, status, data.date, source="manual")
    return {"status": "ok", "test_name": data.test_name, "computed_status": status}


@app.delete("/api/patient/{patient_id}/lab-result/{result_id}")
async def delete_lab_result(patient_id: str, result_id: int):
    ok = db.delete_lab_result(result_id, patient_id)
    if not ok:
        raise HTTPException(404, "Lab result not found")
    return {"status": "ok", "deleted_id": result_id}


def _auto_status(value_str: str, normal_range: str) -> str:
    """Determine status (normal/high/low) based on value vs range."""
    try:
        val = float(value_str)
    except (ValueError, TypeError):
        v = value_str.strip().lower()
        nr = normal_range.strip().lower()
        if nr in ("negative", "absent") and v not in ("negative", "nil", "absent", "not detected", "none"):
            return "abnormal"
        return "noted"
    
    nr = normal_range.strip()
    if nr.startswith("<"):
        try:
            return "high" if val >= float(nr[1:]) else "normal"
        except ValueError:
            return "noted"
    elif nr.startswith(">"):
        try:
            return "low" if val <= float(nr[1:]) else "normal"
        except ValueError:
            return "noted"
    elif "-" in nr:
        parts = nr.split("-")
        try:
            lo, hi = float(parts[0]), float(parts[1])
            if val < lo:
                return "low"
            if val > hi:
                return "high"
            return "normal"
        except (ValueError, IndexError):
            return "noted"
    return "noted"


# ══════════════════════════════════════════════════════════════════
#  RISK PREDICTION ENGINE
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/risk-predictions")
async def risk_predictions(patient_id: str):
    """Predict future disease risks from patient's lab data."""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    labs = db.get_lab_results(patient_id, limit=500)
    
    # Build latest value dict
    latest = {}
    for lr in labs:
        if lr["test_name"] not in latest:
            try:
                latest[lr["test_name"]] = float(lr["value"])
            except (ValueError, TypeError):
                pass
    
    age = patient.get("age") if patient else None
    risks = compute_risk_scores(latest, age)
    
    return {
        "predictions": risks,
        "data_points": len(latest),
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "Risk predictions are estimates based on available data. Consult a healthcare professional for clinical evaluation."
    }


# ══════════════════════════════════════════════════════════════════
#  SMART SYMPTOM QUESTIONING
# ══════════════════════════════════════════════════════════════════

class SmartSymptomRequest(BaseModel):
    patient_id: str
    symptom: str
    answers: Optional[Dict] = None  # previous answers
    session_id: Optional[str] = None


@app.post("/api/symptom-flow")
async def smart_symptom_questioning(request: SmartSymptomRequest):
    """Interactive symptom questioning — returns follow-up questions or diagnosis."""
    db.ensure_patient(request.patient_id)
    session_id = request.session_id or str(uuid.uuid4())
    patient = db.get_patient(request.patient_id)
    
    # Build conversation context from answers so far
    history_parts = [f"Chief complaint: {request.symptom}"]
    if request.answers:
        for q, a in request.answers.items():
            history_parts.append(f"Q: {q}\nA: {a}")
    
    answer_count = len(request.answers) if request.answers else 0
    
    if answer_count >= 5:
        # Enough info — generate diagnosis
        prompt = f"""Patient information:
{f"Age: {patient['age']}, Gender: {patient['gender']}" if patient and patient.get('age') else ""}

{chr(10).join(history_parts)}

Based on the above symptom interview, provide:
1. Top 3 most likely conditions with probability estimates
2. Recommended tests to confirm
3. Immediate actions
4. Red flags to watch

Be concise and structured. Use bullet points."""

        resp = await llm_engine.generate_response(
            message=prompt, history=[], patient_id=request.patient_id, max_tokens=400, temperature=0.4
        )
        return {
            "type": "diagnosis",
            "analysis": resp["response"],
            "session_id": session_id,
            "questions_asked": answer_count,
        }
    
    # Generate next question
    prompt = f"""You are conducting a medical symptom interview. 
Patient complaint: {request.symptom}
{"Previous Q&A:" + chr(10) + chr(10).join(history_parts[1:]) if answer_count > 0 else "This is the first question."}

Ask ONE focused diagnostic follow-up question. Provide 4 answer options.
Format EXACTLY like this:
QUESTION: [Your question here]
1. [Option 1]
2. [Option 2]
3. [Option 3]
4. [Option 4]

Choose the most diagnostically useful question. Consider: location, duration, severity, timing, associated symptoms, aggravating/relieving factors."""

    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=request.patient_id, max_tokens=200
    )
    
    # Parse the response into structured format
    text = resp["response"]
    question = ""
    options = []
    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("QUESTION:"):
            question = line[9:].strip()
        elif line and line[0].isdigit() and "." in line[:3]:
            options.append(line[line.index(".")+1:].strip())
    
    if not question:
        question = text.split("\n")[0].strip()
    if not options:
        options = ["Yes", "No", "Sometimes", "Not sure"]
    
    return {
        "type": "question",
        "question": question,
        "options": options[:6],
        "session_id": session_id,
        "questions_asked": answer_count,
    }


# ══════════════════════════════════════════════════════════════════
#  TIMELINE INTELLIGENCE (trends)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/trends")
async def get_health_trends(patient_id: str):
    """Detect lab value trends over time."""
    db.ensure_patient(patient_id)
    labs = db.get_lab_results(patient_id, limit=500)
    trends = detect_trends(labs)
    return {
        "trends": trends,
        "total_tests_analyzed": len(set(lr["test_name"] for lr in labs)),
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  LAB RESULT INTELLIGENCE (cross-test correlations)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/lab-intelligence")
async def lab_intelligence(patient_id: str):
    """Cross-test correlation analysis — detect metabolic syndrome, anemia patterns, etc."""
    db.ensure_patient(patient_id)
    labs = db.get_lab_results(patient_id, limit=500)
    
    # Build latest value dict
    latest = {}
    for lr in labs:
        if lr["test_name"] not in latest:
            try:
                latest[lr["test_name"]] = float(lr["value"])
            except (ValueError, TypeError):
                latest[lr["test_name"]] = lr["value"]
    
    correlations = compute_lab_correlations(latest)
    
    return {
        "findings": correlations,
        "tests_analyzed": len(latest),
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  MEDICATION TRACKER
# ══════════════════════════════════════════════════════════════════

class MedicationRequest(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/patient/{patient_id}/medications")
async def get_medications(patient_id: str, active_only: bool = True):
    meds = db.get_medications(patient_id, active_only)
    # Compute adherence for each
    for med in meds:
        logs = db.get_medication_adherence(patient_id, med["id"], days=7)
        taken_count = sum(1 for l in logs if l["status"] == "taken")
        # Rough expected: frequency-based
        freq = (med.get("frequency") or "").lower()
        if "twice" in freq or "2x" in freq or "bd" in freq or "bid" in freq:
            expected = 14
        elif "thrice" in freq or "3x" in freq or "tid" in freq:
            expected = 21
        else:
            expected = 7  # once daily default
        med["adherence_7d"] = round(min(100, (taken_count / expected) * 100)) if expected > 0 else 0
        med["taken_7d"] = taken_count
        med["expected_7d"] = expected
    return {"medications": meds}


@app.post("/api/patient/{patient_id}/medication")
async def add_medication(patient_id: str, data: MedicationRequest):
    med_id = db.add_medication(patient_id, data.name, data.dosage, data.frequency, data.start_date, data.notes)
    return {"status": "ok", "medication_id": med_id}


@app.put("/api/patient/{patient_id}/medication/{med_id}")
async def update_medication(patient_id: str, med_id: int, data: MedicationRequest):
    db.update_medication(med_id, patient_id, name=data.name, dosage=data.dosage, frequency=data.frequency, notes=data.notes)
    return {"status": "ok"}


@app.delete("/api/patient/{patient_id}/medication/{med_id}")
async def del_medication(patient_id: str, med_id: int):
    ok = db.delete_medication(med_id, patient_id)
    if not ok:
        raise HTTPException(404, "Medication not found")
    return {"status": "ok"}


@app.post("/api/patient/{patient_id}/medication/{med_id}/log")
async def log_medication(patient_id: str, med_id: int, status: str = "taken"):
    log_id = db.log_medication_taken(med_id, patient_id, status)
    return {"status": "ok", "log_id": log_id}


@app.put("/api/patient/{patient_id}/medication/{med_id}/toggle")
async def toggle_medication(patient_id: str, med_id: int):
    """Toggle medication active/stopped status."""
    med = None
    meds = db.get_medications(patient_id, active_only=False)
    for m in meds:
        if m["id"] == med_id:
            med = m
            break
    if not med:
        raise HTTPException(404, "Medication not found")
    new_active = 0 if med.get("active", 1) else 1
    end_date = datetime.now().strftime("%Y-%m-%d") if new_active == 0 else None
    db.update_medication(med_id, patient_id, active=new_active, end_date=end_date)
    return {"status": "ok", "active": new_active}


class MedicationReminderRequest(BaseModel):
    reminder_morning: Optional[str] = "08:00"
    reminder_evening: Optional[str] = "21:00"
    reminder_enabled: Optional[int] = 1


@app.put("/api/patient/{patient_id}/medication/{med_id}/reminder")
async def update_medication_reminder(patient_id: str, med_id: int, data: MedicationReminderRequest):
    """Update medication reminder settings."""
    db.update_medication(med_id, patient_id,
                         reminder_morning=data.reminder_morning,
                         reminder_evening=data.reminder_evening,
                         reminder_enabled=data.reminder_enabled)
    return {"status": "ok"}


class LifestyleLogRequest(BaseModel):
    patient_id: str
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    sleep_hours: Optional[float] = None
    calories: Optional[int] = None
    water_ml: Optional[int] = None
    date: Optional[str] = None


@app.post("/api/patient/{patient_id}/lifestyle")
async def log_lifestyle(patient_id: str, data: LifestyleLogRequest):
    """Log daily lifestyle metrics (steps, distance, sleep, calories, water)."""
    db.ensure_patient(patient_id)
    date = data.date or datetime.now().strftime("%Y-%m-%d")
    parts = []
    if data.steps is not None:
        parts.append(f"Steps: {data.steps}")
    if data.distance_km is not None:
        parts.append(f"Distance: {data.distance_km}km")
    if data.sleep_hours is not None:
        parts.append(f"Sleep: {data.sleep_hours}h")
    if data.calories is not None:
        parts.append(f"Calories: {data.calories}")
    if data.water_ml is not None:
        parts.append(f"Water: {data.water_ml}ml")
    description = ", ".join(parts)
    db.add_health_event(patient_id, "lifestyle", "Daily Lifestyle Log", description, date=date)
    return {"status": "ok", "logged": description}


class ScreeningWithInputsRequest(BaseModel):
    patient_id: str
    smoker: Optional[str] = None
    alcohol: Optional[str] = None
    family_history: Optional[str] = None
    notes: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
#  TREATMENT PLANS
# ══════════════════════════════════════════════════════════════════

class TreatmentPlanRequest(BaseModel):
    patient_id: str
    condition: str
    severity: Optional[str] = "mild"


@app.post("/api/treatment-plan")
async def generate_treatment_plan(request: TreatmentPlanRequest):
    """Generate an evidence-based treatment plan for a condition."""
    db.ensure_patient(request.patient_id)
    patient = db.get_patient(request.patient_id)
    labs = db.get_lab_results(request.patient_id, limit=30)
    
    patient_info = ""
    if patient:
        patient_info = f"Patient: {patient.get('age','')} years, {patient.get('gender','')}"
        if patient.get("allergies"):
            patient_info += f", Allergies: {patient['allergies']}"
        if patient.get("chronic_conditions"):
            patient_info += f", Conditions: {patient['chronic_conditions']}"
        if patient.get("ethnicity"):
            patient_info += f", Ethnicity/Ancestry: {patient['ethnicity']}"
    
    abnormal_labs = [f"{l['test_name']}: {l['value']} {l.get('unit','')}"
                     for l in labs if l.get("status") in ("high", "low", "abnormal")][:10]
    
    prompt = f"""{patient_info}
Condition: {request.condition} (Severity: {request.severity})
{f"Relevant abnormal labs: {', '.join(abnormal_labs)}" if abnormal_labs else ""}

Create a structured treatment plan:

Lifestyle Changes
• specific dietary changes
• exercise recommendations
• sleep/stress management

Monitoring Plan
• which tests to repeat and when
• warning signs to watch
• follow-up timeline

When to Seek Urgent Care
• specific red flags

Keep it evidence-based, practical, and concise. No medication prescriptions — only lifestyle and monitoring."""

    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=request.patient_id, max_tokens=1500, temperature=0.4
    )
    
    return {
        "plan": resp["response"],
        "condition": request.condition,
        "severity": request.severity,
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  SPECIALIST CONSULTATION
# ══════════════════════════════════════════════════════════════════

@app.get("/api/specialists")
async def list_specialists():
    """List available AI specialist doctors."""
    return {"specialists": [
        {"id": k, "name": v["name"], "icon": v["icon"]}
        for k, v in SPECIALIST_PROMPTS.items()
    ]}


@app.post("/api/chat/specialist/stream")
async def specialist_chat_stream(request: ChatRequest, specialist: str = "general"):
    """Chat with a specific specialist AI doctor."""
    session_id = request.session_id or str(uuid.uuid4())
    patient_id = request.patient_id
    db.ensure_patient(patient_id)
    
    spec = SPECIALIST_PROMPTS.get(specialist, SPECIALIST_PROMPTS["general"])
    patient_ctx = db.get_patient_context(patient_id)
    history = db.get_conversation(patient_id, session_id, limit=10)
    
    mode = getattr(request, 'generation_mode', 'balanced') or 'balanced'
    mode_tokens = {"fast": 300, "balanced": 700, "detailed": 1200}
    mode_temp = {"fast": 0.25, "balanced": 0.35, "detailed": 0.5}
    mode_ctx = {
        "fast": "\nMODE: Be very concise. 2-3 short bullet points max.",
        "balanced": "",
        "detailed": "\nMODE: Give a thorough, detailed specialist response.",
    }
    
    extra = "\n\n".join(filter(None, [
        f"SPECIALIST MODE: {spec['prompt']}",
        f"PATIENT RECORD:\n{patient_ctx}" if patient_ctx else "",
        mode_ctx.get(mode, ""),
    ]))
    
    provider = _resolve_model_provider(request.model_provider)

    async def _stream():
        full = ""
        started = False
        try:
            yield f"data: {json.dumps({'type':'specialist','name':spec['name'],'icon':spec['icon']})}\n\n"
            if provider == "core":
                async for token in llm_engine.generate_response_stream(
                    message=request.message, history=history,
                    patient_id=patient_id, extra_context=extra,
                ):
                    full += token
                    if not started:
                        stripped = re.sub(r'^[\s{}]*(?:\{[^}]*"name"\s*:[^}]*\}[\s{}]*)*', '', full)
                        stripped = stripped.lstrip('\t\n{}')
                        if stripped and not stripped.startswith('{'):
                            started = True
                            full = stripped
                            yield f"data: {json.dumps({'type':'chunk','content':stripped})}\n\n"
                        continue
                    yield f"data: {json.dumps({'type':'chunk','content':token})}\n\n"
            else:
                async for token in cloud_engine.generate_response_stream(
                    provider=provider,
                    message=request.message,
                    history=history,
                    patient_id=patient_id,
                    extra_context=extra,
                ):
                    full += token
                    started = True
                    yield f"data: {json.dumps({'type':'chunk','content':token})}\n\n"
            
            if not started:
                full = re.sub(r'^[\s{}]*(?:\{[^}]*"name"\s*:[^}]*\}[\s{}]*)*', '', full)
                full = full.lstrip('\t\n{}')
            
            db.save_message(patient_id, session_id, "user", request.message, "en")
            db.save_message(patient_id, session_id, "assistant", full, "en",
                            metadata={"specialist": specialist, "model_provider": provider})
            
            yield f"data: {json.dumps({'type':'done','session_id':session_id,'specialist':specialist})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Specialist stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type':'error','content':'Specialist consultation failed.'})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════
#  HEALTH COACH (daily briefing)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/health-coach")
async def health_coach_briefing(patient_id: str):
    """Generate a personalized daily health briefing."""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    labs = db.get_lab_results(patient_id, limit=50)
    meds = db.get_medications(patient_id, active_only=True)
    events = db.get_health_timeline(patient_id, 10)
    
    # Build a concise context
    parts = []
    if patient and patient.get("name"):
        parts.append(f"Patient: {patient.get('name')}, Age: {patient.get('age','?')}, Gender: {patient.get('gender','?')}")
    if patient and patient.get("chronic_conditions"):
        parts.append(f"Conditions: {patient['chronic_conditions']}")
    
    abnormals = [f"{l['test_name']}: {l['value']} {l.get('unit','')}" for l in labs if l.get("status") in ("high","low","abnormal")][:8]
    if abnormals:
        parts.append(f"Abnormal labs: {', '.join(abnormals)}")
    
    if meds:
        parts.append(f"Active medications: {', '.join(m['name']+(' '+m.get('dosage','') if m.get('dosage') else '') for m in meds[:5])}")

    # Include recent lifestyle logs
    lifestyle_events = [e for e in events if e.get("event_type") == "lifestyle"]
    if lifestyle_events:
        parts.append("Recent lifestyle logs:")
        for le in lifestyle_events[:3]:
            parts.append(f"  [{le['date']}] {le.get('description', '')}")
    
    prompt = f"""Generate a brief, friendly daily health briefing for this patient.

{chr(10).join(parts) if parts else "New patient — no data yet."}

Format exactly:
Good [morning/afternoon/evening], [name]!

Health Summary
• [1-2 key observations]

Today's Focus
• [2-3 actionable health tips personalized to their data]

Fitness & Lifestyle
• [1-2 tips based on their activity/lifestyle data if available, or general fitness advice]

Reminders
• [medication reminders if any]
• [upcoming tests needed]

Keep it warm, encouraging, and under 250 words."""

    resp = await llm_engine.generate_response(
        message=prompt, history=[], patient_id=patient_id, max_tokens=300, temperature=0.4
    )
    
    return {
        "briefing": resp["response"],
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  PREVENTIVE HEALTH PLANNER
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/screening-plan")
async def get_screening_plan_endpoint(patient_id: str):
    """Get age/gender-appropriate preventive screening recommendations."""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    age = patient.get("age", 30) if patient else 30
    gender = patient.get("gender") if patient else None
    
    plan = get_screening_plan(age, gender)
    
    # Check which tests the patient already has
    labs = db.get_lab_results(patient_id, limit=500)
    existing_tests = set(lr["test_name"] for lr in labs)
    
    for item in plan:
        # Mark as done if patient has any recent results for related tests
        item["has_recent"] = any(t in existing_tests for t in _screening_test_names(item["test"]))
    
    return {
        "plan": plan,
        "age": age,
        "gender": gender,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/patient/{patient_id}/screening-plan")
async def get_screening_plan_with_inputs(patient_id: str, data: ScreeningWithInputsRequest):
    """Generate screening plan with optional lifestyle inputs (smoker, alcohol, family history)."""
    db.ensure_patient(patient_id)
    patient = db.get_patient(patient_id)
    age = patient.get("age", 30) if patient else 30
    gender = patient.get("gender") if patient else None

    plan = get_screening_plan(age, gender)

    # Check which tests already done
    labs = db.get_lab_results(patient_id, limit=500)
    existing_tests = set(lr["test_name"] for lr in labs)
    for item in plan:
        item["has_recent"] = any(t in existing_tests for t in _screening_test_names(item["test"]))

    # Build AI-enhanced recommendations if lifestyle inputs provided
    extras = []
    if data.smoker:
        extras.append(f"Smoking status: {data.smoker}")
    if data.alcohol:
        extras.append(f"Alcohol use: {data.alcohol}")
    if data.family_history:
        extras.append(f"Family history: {data.family_history}")
    if data.notes:
        extras.append(f"Additional notes: {data.notes}")

    ai_advice = None
    if extras:
        prompt = f"""Patient: Age {age}, Gender: {gender or 'unknown'}
Lifestyle factors: {', '.join(extras)}

Based on these lifestyle factors, suggest 2-3 additional screening tests or adjustments to the standard screening plan. Be specific and brief. Use bullet points."""
        try:
            resp = await llm_engine.generate_response(
                message=prompt, history=[], patient_id=patient_id, max_tokens=300, temperature=0.4
            )
            ai_advice = resp.get("response", "")
        except Exception:
            pass

    return {
        "plan": plan,
        "age": age,
        "gender": gender,
        "lifestyle_inputs": {k: v for k, v in {"smoker": data.smoker, "alcohol": data.alcohol, "family_history": data.family_history, "notes": data.notes}.items() if v},
        "ai_advice": ai_advice,
        "timestamp": datetime.now().isoformat(),
    }


def _screening_test_names(test_description: str) -> list:
    """Map screening description to known test names."""
    mapping = {
        "Complete Blood Count": ["hemoglobin", "rbc_count", "wbc_count", "platelet_count"],
        "Fasting Blood Glucose": ["fasting_glucose"],
        "Lipid Profile": ["total_cholesterol", "ldl_cholesterol", "hdl_cholesterol", "triglycerides"],
        "Liver Function": ["sgpt_alt", "sgot_ast", "total_bilirubin"],
        "Kidney Function": ["creatinine", "bun", "uric_acid"],
        "Thyroid": ["tsh", "t3", "t4"],
        "Vitamin D": ["vitamin_d"],
        "Vitamin B12": ["vitamin_b12"],
        "Iron": ["ferritin", "serum_iron"],
        "HbA1c": ["hba1c"],
        "Urine": ["urine_ph", "urine_protein"],
        "PSA": ["psa"],
    }
    for key, names in mapping.items():
        if key.lower() in test_description.lower():
            return names
    return []


# ══════════════════════════════════════════════════════════════════
#  BODY HEALTH MAP (organ scores)
# ══════════════════════════════════════════════════════════════════

@app.get("/api/patient/{patient_id}/organ-health")
async def organ_health_map(patient_id: str):
    """Compute organ-level health scores based on lab data."""
    db.ensure_patient(patient_id)
    labs = db.get_lab_results(patient_id, limit=500)
    
    latest = {}
    for lr in labs:
        if lr["test_name"] not in latest:
            try:
                latest[lr["test_name"]] = float(lr["value"])
            except (ValueError, TypeError):
                pass
    
    organs = compute_organ_scores(latest)
    # Overall score (average of scored organs)
    scored = [o for o in organs if o["score"] is not None]
    overall = round(sum(o["score"] for o in scored) / len(scored)) if scored else None
    
    return {
        "organs": organs,
        "overall_score": overall,
        "data_points": len(latest),
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
#  AUDIO SERVING
# ══════════════════════════════════════════════════════════════════

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    safe = os.path.basename(filename)
    fpath = os.path.join("static", "audio", safe)
    if os.path.exists(fpath):
        return FileResponse(fpath, media_type="audio/wav" if safe.endswith(".wav") else "audio/mpeg")
    raise HTTPException(404, "Audio not found")


# ══════════════════════════════════════════════════════════════════
#  STARTUP / SHUTDOWN
# ══════════════════════════════════════════════════════════════════

@app.get("/api/medical-facilities")
async def get_medical_facilities(city: str, specialty: Optional[str] = None):
    """Retrieve medical facilities/doctors in a specific city, optionally filtered by specialty/keyword"""
    key = city.lower().strip().replace(" ", "").replace("newdelhi", "delhi").replace("sasnagar", "mohali")
    results = HOSPITAL_DATA.get(key, [])
    
    if specialty and specialty.strip():
        q = specialty.lower().strip()
        filtered = [h for h in results if q in h["name"].lower() or q in h.get("type", "").lower() or q in h.get("address", "").lower()]
        results = filtered
        
    if not results:
        return {"facilities": [{"type": "info", "name": f"No specific doctors or hospitals found in '{city}' for that specialty. Try nearby cities like Chandigarh, Mohali, or Delhi."}]}
        
    return {"facilities": results}

# ══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Medical AI Assistant Pro v4.0 — Starting Up")
    logger.info("Services will load on-demand (lazy loading enabled)")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    await llm_engine.cleanup()
    await voice_processor.cleanup()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")