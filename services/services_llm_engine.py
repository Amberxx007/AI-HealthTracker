# pyre-ignore-all-errors[21]
"""
Medical LLM Engine
Advanced conversational AI with medical knowledge and safety
"""

import requests
import json
import os
import threading
from typing import List, Dict, Optional, AsyncGenerator
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from utils.utils_logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()


class MedicalLLMEngine:
    """
    Enterprise Medical LLM with:
    - Conversation memory
    - Safety guardrails
    - Medical expertise
    - Multi-turn dialogue
    - Token streaming for fast perceived response
    """
    
    # On Railway, Llama server doesn't exist - only use if LLAMA_BASE_URL env var is explicitly set
    # Local development can set LLAMA_BASE_URL=http://localhost:8080 in .env or environment
    DEFAULT_LLAMA_BASE_URL = ""  # Empty by default — fallback to cloud providers
    MEDIUM_SYSTEM_PROMPT = """You are Best Dr. AI, a professional and caring medical assistant.

RULES:
- Reply in the SAME language the patient uses.
- Use bullet points (•) for lists, NOT asterisks or markdown.
- Use **bold** to highlight important timings, durations, dosage warnings, and critical reminders.
- Never diagnose definitively. Say "this could indicate" or "one possibility is".
- Never prescribe specific medication dosages.
- Always recommend professional consultation for serious symptoms.
- Scan for red-flag / danger signs first. If present, START with ⚠️ **DANGER SIGN DETECTED**.
- For health complaints, provide differential diagnoses with one-line reasoning each.
- At the END, add "**Questions to help narrow the diagnosis:**" with 3-5 targeted questions.
- Give Home Remedies and food advice when applicable.
- Suggest which type of specialist the patient should see when relevant.
- Keep response under 350 words unless detail is requested.

IMPORTANT: You are a TEXT assistant. NEVER output JSON, function calls, tool calls, or code."""

    COMPACT_SYSTEM_PROMPT = (
        "You are Best Dr. AI, a professional medical assistant. Reply in the user's language. "
        "Use bullet points (•) for lists, **bold** for key terms. "
        "Never diagnose definitively or prescribe dosages. "
        "Provide differential diagnoses with reasoning. "
        "End with targeted diagnostic questions. "
        "If red-flag symptoms, start with ⚠️ DANGER SIGN warning. "
        "NEVER output JSON or function calls — reply in plain text only."
    )
    
    SYSTEM_PROMPT = """You are Best Dr. AI, a professional and caring medical assistant.

RULES:
- Reply in the SAME language the patient uses.
- Use bullet points (•) for lists. Use **bold** for key terms, timings, dosages, warnings.
- Never diagnose definitively — say "this could indicate" or "one possibility is".
- Never prescribe specific dosages. Recommend professional consultation for serious symptoms.
- Be direct. Respond naturally. Simple questions get simple answers.
- Explain medical terms simply. Suggest relevant specialists when appropriate.
- You are a HEALTH assistant — answer ALL health-related questions including lifestyle, diet, nutrition, exercise, sleep, wellness, mental health, and daily habits.

DANGER TRIAGE (check first):
- Scan for red flags: sudden onset, worst-ever pain, one-sided weakness, vision changes, chest pain at rest, high fever with rash/stiff neck, unexplained weight loss, blood in stool/urine/vomit, severe breathlessness, confusion/falls in elderly, facial/throat swelling.
- If present, START with: "⚠️ **DANGER SIGN DETECTED** — [reason]. Seek immediate medical attention."

LIFESTYLE & WELLNESS (answer these fully — do NOT deflect):
- When patients mention daily habits (morning drinks, routines, exercise, diet), provide health impact analysis.
- For foods/beverages: explain health benefits, risks, recommended frequency, best timing, and who should avoid them.
- For exercise: explain benefits, intensity guidance, precautions, and how it relates to their health profile.
- For sleep patterns: explain impact on health, optimal duration, and improvement tips.
- For stress/mental wellness: provide practical coping strategies and lifestyle modifications.
- If a patient says "I drink X" or "I eat X" or "I do X every morning/day", ALWAYS explain the health impact of that specific item. Never say you don't know what they're referring to — analyze the health properties of whatever they mention.

GENERAL HEALTH KNOWLEDGE:
- Answer questions about any food, drink, supplement, herb, spice, or natural remedy.
- Explain nutritional content, health benefits, potential side effects, and drug interactions.
- Cover topics like hydration, weight management, immunity, gut health, skin health, hair health.
- If a patient asks about a specific product or brand, discuss the general category's health effects.

CLINICAL REASONING:
- For health complaints provide: (1) Symptoms noted (2) Reasoning — what symptoms suggest together (3) 2-3 differential diagnoses with one-line reasoning each (3+ for elderly) (4) Stage/classify if data available (BP stages, HbA1c, CKD, NYHA, BMI) (5) Contributing factors: age, gender, lifestyle, stress, sleep, occupation, diet, season (6) Risk factors: family history, pre-existing conditions, smoking/alcohol.
- Classify numbers immediately (BP, sugar, weight).

HOME REMEDIES (always include when applicable):
- Give 3-5 specific remedies: dietary (specific teas, soups, spices), herbal/natural (oils, herbs), lifestyle (sleep position, breathing, exercise), topical (compress, gargle, steam inhalation).
- List specific foods to EAT and foods to AVOID (3-5 each). Be specific — not generic.

DRUG INTERACTIONS (when medications mentioned):
- Explain interaction mechanism. Give drug-specific timing (WITH food: NSAIDs/metformin; EMPTY stomach: levothyroxine; spacing: antacids 2h from antibiotics; time-of-day: statins at night, BP meds morning). Never default to generic "morning/night".
- Cover food-drug interactions, contraindications, side effects to watch, duration.

DIAGNOSTIC QUESTIONS:
- End clinical responses with "**Questions to help narrow the diagnosis:**" — 3-5 specific questions that rule in/out differentials. Don't re-ask answered questions.

IMPORTANT: You are a TEXT assistant. NEVER output JSON, function calls, or code."""

    def __init__(self, model_name: str = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"):
        """Initialize LLM engine"""
        self.model_name = model_name
        self.max_history = 10  # Keep last 10 exchanges
        self.n_ctx = 4096  # Default — matches llama-server -c 4096 in start_all.bat
        self.default_provider = os.getenv("DEFAULT_MODEL_PROVIDER", "").strip().lower()
        # Trim whitespace to avoid malformed URLs (e.g. "http://localhost:8081 ")
        self.llama_base_url = os.getenv("LLAMA_BASE_URL", self.DEFAULT_LLAMA_BASE_URL).strip().rstrip("/")
        
        # Only construct URLs if llama_base_url is configured
        if self.llama_base_url:
            self.llama_chat_url = f"{self.llama_base_url}/v1/chat/completions"
            self.llama_props_url = f"{self.llama_base_url}/props"
            self.llama_health_url = f"{self.llama_base_url}/health"
            logger.info(f"Medical LLM endpoint: {self.llama_base_url}")
        else:
            self.llama_chat_url = None
            self.llama_props_url = None
            self.llama_health_url = None
            logger.info("Llama server not configured - will use cloud providers for LLM")
        
        # Semaphore for parallel request handling — allows queueing
        # llama-server handles one at a time, but we queue gracefully
        self._semaphore = asyncio.Semaphore(3)
        self._request_counter = 0
        self._lock = asyncio.Lock()
        logger.info(f"Medical LLM initialized with model: {model_name}")

    def _preferred_provider(self) -> str:
        """Choose cloud first when configured, otherwise use local if healthy."""
        cloud_order = [self.default_provider, "openai", "gemini", "anthropic"]
        for provider in cloud_order:
            if provider in CloudModelEngine.PROVIDERS and self._cloud_key_available(provider):
                if provider != "core":
                    return provider
        if self.check_health():
            return "core"
        for provider in ("openai", "gemini", "anthropic"):
            if self._cloud_key_available(provider):
                return provider
        # If no cloud provider available and Llama not healthy, return "core" but it will fail
        # This is expected behavior - user should configure a cloud provider on Railway
        return "core"

    @staticmethod
    def _cloud_key_available(provider: str) -> bool:
        info = CloudModelEngine.PROVIDERS.get(provider)
        if not info:
            return False
        return bool(os.environ.get(info["env_key"], "").strip())

    async def _generate_cloud_text(
        self,
        provider: str,
        message: str,
        history: List[Dict],
        patient_id: str,
        temperature: float,
        max_tokens: int,
        extra_context: str,
    ) -> Dict:
        cloud_engine = CloudModelEngine()
        response_text = ""
        async for token in cloud_engine.generate_response_stream(
            provider=provider,
            message=message,
            history=history,
            patient_id=patient_id,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_context=extra_context,
        ):
            response_text += token
        return {
            "response": response_text.strip() or "I can help with that, but I need a little more detail.",
            "confidence": 0.9,
            "model": provider,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _detect_context_size(self):
        """Query llama-server for actual context window size."""
        if not self.llama_props_url:
            # Llama not configured, use default
            logger.info("Llama not configured, using default context window: 2048 tokens")
            return
        
        try:
            r = requests.get(self.llama_props_url, timeout=5)
            data = r.json()
            n_ctx = data.get("default_generation_settings", {}).get("n_ctx", 2048)
            self.n_ctx = n_ctx
            logger.info(f"LLM context window: {n_ctx} tokens")
        except Exception:
            logger.warning("Could not detect n_ctx, using default 2048")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: ~3.5 chars per token for English."""
        return max(1, len(text) // 3)

    def _trim_messages_to_fit(self, messages: List[Dict], max_tokens: int) -> tuple:
        """Trim messages so prompt + max_tokens fits in n_ctx.
        Returns (trimmed_messages, adjusted_max_tokens)."""
        prompt_budget = self.n_ctx - 64  # small safety margin

        # Estimate current prompt token count
        prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)

        # If everything fits, great
        if prompt_tokens + max_tokens <= prompt_budget:
            return messages, max_tokens

        # First: reduce max_tokens to at most half the context
        max_tokens = min(max_tokens, prompt_budget // 2)

        # Still too big? Trim extra_context from system message
        if prompt_tokens + max_tokens > prompt_budget:
            sys_msg = messages[0]
            base_prompt = self.SYSTEM_PROMPT
            extra = sys_msg["content"][len(base_prompt):]
            if extra:
                # Keep only what fits
                available_chars = (prompt_budget - max_tokens - sum(
                    self._estimate_tokens(m["content"]) + 4 for m in messages[1:]
                ) - 4) * 3 - len(base_prompt)
                if available_chars < 100:
                    messages[0] = {"role": "system", "content": base_prompt}
                else:
                    messages[0] = {"role": "system", "content": base_prompt + extra[:available_chars]}

        # Recalculate
        prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)

        # Still too big? Drop older history (keep system + last user msg)
        while prompt_tokens + max_tokens > prompt_budget and len(messages) > 2:
            messages.pop(1)  # remove oldest non-system message
            prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)

        # If context is still too large, try the medium prompt first (preserves
        # key formatting rules), then fall back to compact only as last resort.
        if prompt_tokens + max_tokens > prompt_budget and messages:
            messages[0] = {"role": "system", "content": self.MEDIUM_SYSTEM_PROMPT}
            prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)
        if prompt_tokens + max_tokens > prompt_budget and messages:
            messages[0] = {"role": "system", "content": self.COMPACT_SYSTEM_PROMPT}
            prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)

        # If still too big, truncate the final user message to fit the budget.
        if prompt_tokens + max_tokens > prompt_budget and len(messages) >= 2:
            # Assume the last message is the active user message.
            non_user_tokens = sum(
                self._estimate_tokens(m["content"]) + 4 for m in messages[:-1]
            )
            allowed_user_tokens = max(16, prompt_budget - max_tokens - non_user_tokens - 4)
            allowed_user_chars = allowed_user_tokens * 3
            user_content = messages[-1].get("content", "")
            if len(user_content) > allowed_user_chars:
                messages[-1]["content"] = user_content[-allowed_user_chars:]
            prompt_tokens = sum(self._estimate_tokens(m["content"]) + 4 for m in messages)

        # Final guard: reduce generation budget instead of sending an invalid request.
        if prompt_tokens + max_tokens > prompt_budget:
            max_tokens = max(64, prompt_budget - prompt_tokens)

        logger.info(f"Context fit: ~{prompt_tokens} prompt tokens + {max_tokens} gen tokens / {self.n_ctx} ctx")
        return messages, max_tokens

    async def initialize(self):
        """Check LLM connectivity"""
        if not self.llama_health_url:
            logger.info("Llama server not configured - will use cloud providers")
            return
        
        try:
            response = requests.get(
                self.llama_health_url,
                timeout=5
            )
            logger.info("LLM server connection verified")
            self._detect_context_size()
        except Exception as e:
            logger.warning(f"LLM server not accessible: {e}")
            logger.warning("Will retry on first request")
    
    async def generate_response(
        self,
        message: str,
        history: List[Dict],
        patient_id: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_context: str = ""
    ) -> Dict:
        """
        Generate medical response using streaming internally to avoid timeout.
        Collects all tokens from the streaming API and returns the full response.
        Uses semaphore for parallel request queueing.
        """
        preferred_provider = self._preferred_provider()
        if preferred_provider != "core":
            return await self._generate_cloud_text(
                preferred_provider, message, history, patient_id, temperature, max_tokens, extra_context
            )

        # If we reach here with preferred_provider == "core", ensure Llama is actually configured
        if not self.llama_chat_url:
            logger.warning("Llama not configured and no cloud provider available - returning error response")
            return {
                "response": "I'm unable to process your request at this moment. Please try again later or contact support.",
                "confidence": 0.1,
                "model": "unavailable",
                "timestamp": datetime.now().isoformat(),
            }

        async with self._semaphore:
            async with self._lock:
                self._request_counter += 1
                req_id = self._request_counter
            logger.info(f"[req-{req_id}] Starting LLM generation for patient {patient_id}")
            try:
                system_content = self.SYSTEM_PROMPT
                if extra_context:
                    system_content += "\n\n" + extra_context

                messages = [
                    {"role": "system", "content": system_content}
                ]
                
                if history:
                    recent_history = history[-self.max_history:]
                    for msg in recent_history:
                        messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
                
                messages.append({
                    "role": "user",
                    "content": message
                })

                # Trim to fit context window
                messages, max_tokens = self._trim_messages_to_fit(messages, max_tokens)
                
                # Use streaming internally to avoid timeout on long generations
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "stream": True,
                    "stop": [
                        "\n\nPatient:", "\n\nUser:", "\n\nHuman:",
                        "<|eot_id|>", "<|end|>", "<|python_tag|>"
                    ],
                }
                
                logger.info(f"[req-{req_id}] Generating response for patient {patient_id}")

                response = requests.post(
                    self.llama_chat_url,
                    json=payload,
                    stream=True,
                    timeout=300
                )
                response.raise_for_status()
                
                # Collect streamed tokens into full response
                llm_response = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8")
                    if not decoded.startswith("data: "):
                        continue
                    data = decoded[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if token:
                            llm_response += token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                
                llm_response = llm_response.strip()
                
                if not llm_response:
                    return self._fallback_response("error")

                llm_response = self._post_process_response(llm_response)
                
                logger.info(f"[req-{req_id}] Generated response: {llm_response[:100]}...")
                
                return {
                    "response": llm_response,
                    "confidence": 0.9,
                    "model": self.model_name,
                    "timestamp": datetime.now().isoformat()
                }
                
            except requests.exceptions.Timeout:
                logger.error(f"[req-{req_id}] LLM request timeout")
                return self._fallback_response("timeout")
                
            except requests.exceptions.ConnectionError:
                logger.error(f"[req-{req_id}] Cannot connect to LLM server")
                return self._fallback_response("connection_error")
                
            except Exception as e:
                logger.error(f"[req-{req_id}] LLM generation error: {e}", exc_info=True)
                return self._fallback_response("error")
    
    async def generate_response_stream(
        self,
        message: str,
        history: List[Dict],
        patient_id: str,
        temperature: float = 0.35,
        max_tokens: int = 1024,
        extra_context: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response token by token for real-time display.
        Uses semaphore for parallel request queueing.
        """
        preferred_provider = self._preferred_provider()
        if preferred_provider != "core":
            async for token in CloudModelEngine().generate_response_stream(
                provider=preferred_provider,
                message=message,
                history=history,
                patient_id=patient_id,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_context=extra_context,
            ):
                yield token
            return

        async with self._semaphore:
            system_content = self.SYSTEM_PROMPT
            if extra_context:
                system_content += "\n\n" + extra_context

            messages = [{"role": "system", "content": system_content}]

            if history:
                for msg in history[-self.max_history:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })

            messages.append({"role": "user", "content": message})

            # Trim to fit context window
            messages, max_tokens = self._trim_messages_to_fit(messages, max_tokens)

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9,
                "stream": True,
                "stop": [
                    "\n\nPatient:", "\n\nUser:", "\n\nHuman:",
                    "<|eot_id|>", "<|end|>", "<|python_tag|>"
                ],
            }

            loop = asyncio.get_event_loop()
            q: asyncio.Queue = asyncio.Queue()

            def _stream_worker():
                """Run blocking HTTP streaming in a thread, push chunks to async queue."""
                try:
                    resp = requests.post(
                        self.llama_chat_url, json=payload, stream=True, timeout=120
                    )
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        decoded = line.decode("utf-8")
                        if not decoded.startswith("data: "):
                            continue
                        data = decoded[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            token = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            token = self._sanitize_stream_token(token)
                            if token:
                                loop.call_soon_threadsafe(q.put_nowait, token)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                except Exception as exc:
                    loop.call_soon_threadsafe(
                        q.put_nowait, Exception(str(exc))
                    )
                finally:
                    loop.call_soon_threadsafe(q.put_nowait, None)

            threading.Thread(target=_stream_worker, daemon=True).start()

            emitted_any = False
            emitted_fallback = False

            while True:
                item = await q.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    logger.error(f"Stream error: {item}")
                    emitted_fallback = True
                    yield "\n\nI'm having a little trouble right now. Could you please try again?"
                    break
                emitted_any = True
                yield item

            if not emitted_any and not emitted_fallback:
                yield "I can help with that. Please describe your symptoms briefly (duration, severity, and any warning signs) so I can guide you properly."
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate confidence score from LLM response
        
        Args:
            result: Raw LLM response
            
        Returns:
            Confidence score (0-1)
        """
        try:
            # Check if response has finish_reason
            finish_reason = result["choices"][0].get("finish_reason")
            
            if finish_reason == "stop":
                # Natural completion
                return 0.9
            elif finish_reason == "length":
                # Hit token limit
                return 0.7
            else:
                return 0.8
                
        except Exception:
            return 0.8
    
    @staticmethod
    def _strip_json_artifacts(text: str) -> str:
        """Remove leading JSON tool-call artifacts that Llama 3.1 sometimes emits."""
        import re
        original = text.strip()
        # Strip leading JSON objects like {"name": "...", "parameters": {...}}
        # Handle nested braces in parameters
        cleaned = re.sub(r'^\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*', '', original)
        cleaned = cleaned.lstrip(' \t\n{}').strip()
        # If the entire response is JSON, try to extract any text after it
        if not cleaned and original:
            # Try to find text after closing braces
            match = re.search(r'\}\s*\}?\s*(.+)', original, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
            else:
                # The whole thing is JSON — return empty so fallback kicks in
                cleaned = ""
        return cleaned

    @staticmethod
    def _sanitize_stream_token(token: str) -> str:
        """Remove tool-call JSON fragments from streamed token chunks."""
        import re
        raw = token or ""
        if not raw:
            return ""

        lower_raw = raw.lower()
        # Hard-drop only explicit JSON key fragments, keep normal language tokens
        if any(k in lower_raw for k in ['"name":', '"parameters":', '"arguments":', '"tool_calls":', 'function_call']):
            return ""

        # Fast path: normal language tokens should pass through unchanged,
        # including leading spaces that preserve word boundaries in streaming.
        if not re.search(r'"(name|parameters|arguments|tool_calls)"\s*:|^\s*[\{\}]\s*$', raw, flags=re.IGNORECASE):
            return raw

        pure_patterns = [
            r'^\s*\{\s*"name"\s*:\s*"[^"]*"\s*,?\s*"parameters"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}?\s*$',
            r'^\s*"name"\s*:\s*"[^"]*"\s*,?\s*$',
            r'^\s*"parameters"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}?\s*$',
            r'^\s*"?(arguments|tool_calls)"?\s*:\s*.*$',
        ]
        for pat in pure_patterns:
            if re.match(pat, raw, flags=re.IGNORECASE):
                return ""

        cleaned = raw
        cleaned = re.sub(r'^\s*\{\s*"name"\s*:\s*"[^"]*"\s*,?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^\s*"name"\s*:\s*"[^"]*"\s*,?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^\s*"parameters"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.lstrip('\t\n{},')

        if re.fullmatch(r'[\s\{\}\[\]":,`]+', cleaned or ""):
            return ""

        return cleaned

    def _post_process_response(self, response: str) -> str:
        """Clean LLM response — strip JSON artifacts, preserve line breaks, strip markdown."""
        import re
        # First strip any JSON tool-call artifacts
        response = self._strip_json_artifacts(response)
        # Keep **bold** markers (rendered by frontend), strip other markdown
        response = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', response)  # *italic* → plain (but not **bold**)
        response = re.sub(r'^#+\s*', '', response, flags=re.MULTILINE)  # ## headers → plain
        response = re.sub(r'^[-*]\s+', '• ', response, flags=re.MULTILINE)  # - list → • list
        
        # Collapse 3+ newlines into 2
        response = re.sub(r'\n{3,}', '\n\n', response)

        # If output is only JSON/braces/punctuation artifact, drop it.
        if re.fullmatch(r'[\s\{\}\[\]":,`]+', response or ""):
            response = ""
        
        # Ensure response isn't too short
        if len(response.strip()) < 50:
            if any(ch.isalpha() for ch in response):
                response += "\nCould you tell me more about your symptoms so I can better understand how to help?"
            else:
                response = (
                    "I can help with that. Please share your symptoms, how long they have been present, "
                    "severity (1-10), and any warning signs like fever, vomiting, chest pain, weakness, "
                    "or breathing difficulty."
                )
        
        return response.strip()
    
    def _fallback_response(self, error_type: str) -> Dict:
        """
        Provide fallback response when LLM fails
        
        Args:
            error_type: Type of error
            
        Returns:
            Fallback response dict
        """
        responses = {
            "timeout": "I apologize, but I'm taking a bit longer than usual to respond. Could you please repeat your question?",
            "connection_error": "I'm having trouble connecting to my medical knowledge system. Please try again in a moment.",
            "error": "I encountered an issue processing your request. Could you please rephrase your question?"
        }
        
        return {
            "response": responses.get(error_type, responses["error"]),
            "confidence": 0.5,
            "model": "fallback",
            "timestamp": datetime.now().isoformat(),
            "error": error_type
        }
    
    def check_health(self) -> bool:
        """Check if LLM server is accessible (only if configured)"""
        if not self.llama_base_url:
            # Llama not configured, so it's not healthy, but that's OK
            # (cloud providers will be used instead)
            return False
        
        try:
            response = requests.get(
                self.llama_health_url,
                timeout=3
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Medical LLM engine cleaned up")


# Specialized medical prompt templates

class MedicalPrompts:
    """Collection of specialized medical prompts"""
    
    SYMPTOM_ASSESSMENT = """Based on the patient's symptoms, provide:
1. Possible causes (3-5 common ones)
2. Warning signs to watch for
3. When to seek immediate care
4. Self-care recommendations
5. Questions to ask to better understand

Keep it conversational and empathetic."""

    IMAGE_ANALYSIS = """A patient has shared a medical image showing: {description}

Provide a compassionate response that:
- Acknowledges what they've shared
- Explains what the visible signs might indicate (possibilities, not diagnosis)
- Suggests appropriate next steps
- Recommends consulting a healthcare provider
- Offers reassurance where appropriate

Be gentle and supportive."""

    FOLLOW_UP = """The patient mentioned: {previous_symptom}
Now they're saying: {current_symptom}

Consider:
- Is this a progression?
- Are these related symptoms?
- Does this change the assessment?
- What additional information is needed?

Respond naturally, showing you remember the conversation."""

    EMERGENCY_CONTEXT = """IMPORTANT: The patient mentioned symptoms that could indicate an emergency.

Symptoms: {symptoms}

Provide immediate guidance:
- Acknowledge the seriousness
- Recommend calling emergency services (102)
- What to do while waiting
- Stay calm but firm
- Emphasize urgency without causing panic"""


class CloudModelEngine:
    """
    Routes to cloud LLM providers (OpenAI, Gemini, Anthropic, Groq)
    using the same medical system prompt as the core engine.
    """

    PROVIDERS = {
        "openai": {"env_key": "OPENAI_API_KEY", "label": "GPT-4o"},
        "gemini": {"env_key": "GOOGLE_AI_API_KEY", "label": "Gemini"},
        "anthropic": {"env_key": "ANTHROPIC_API_KEY", "label": "Claude"},
        "groq": {"env_key": "GROQ_API_KEY", "label": "Groq"},
    }

    def __init__(self):
        self.system_prompt = MedicalLLMEngine.SYSTEM_PROMPT
        logger.info("CloudModelEngine initialized")

    def is_available(self, provider: str) -> bool:
        info = self.PROVIDERS.get(provider)
        if not info:
            return False
        key = os.environ.get(info["env_key"], "").strip()
        return bool(key)

    def get_available_providers(self) -> List[Dict]:
        result = []
        for pid, info in self.PROVIDERS.items():
            result.append({
                "id": pid,
                "label": info["label"],
                "available": self.is_available(pid),
            })
        return result

    async def _stream_with_provider(
        self,
        provider: str,
        api_key: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        if provider == "openai":
            async for token in self._stream_openai(api_key, messages, temperature, max_tokens):
                yield token
        elif provider == "gemini":
            async for token in self._stream_gemini(api_key, messages, temperature, max_tokens):
                yield token
        elif provider == "anthropic":
            async for token in self._stream_anthropic(api_key, messages, temperature, max_tokens):
                yield token
        elif provider == "groq":
            async for token in self._stream_groq(api_key, messages, temperature, max_tokens):
                yield token

    def _fallback_order(self, primary_provider: str) -> List[str]:
        ordered = [primary_provider]
        default_provider = os.getenv("DEFAULT_MODEL_PROVIDER", "").strip().lower()
        if default_provider and default_provider in self.PROVIDERS and default_provider not in ordered:
            ordered.append(default_provider)
        for pid in self.PROVIDERS:
            if pid not in ordered:
                ordered.append(pid)
        return [pid for pid in ordered if self.is_available(pid)]

    async def generate_response_stream(
        self,
        provider: str,
        message: str,
        history: List[Dict],
        patient_id: str,
        temperature: float = 0.35,
        max_tokens: int = 1024,
        extra_context: str = "",
    ) -> AsyncGenerator[str, None]:
        info = self.PROVIDERS.get(provider)
        if not info:
            yield "Error: Unknown provider."
            return
        if not self.is_available(provider):
            yield f"⚠️ {info['label']} API key is not configured. Please add your {info['env_key']} to the .env file and restart the server."
            return

        system_content = self.system_prompt
        if extra_context:
            system_content += "\n\n" + extra_context

        messages = [{"role": "system", "content": system_content}]
        if history:
            for msg in history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        messages.append({"role": "user", "content": message})

        attempted = []
        for candidate in self._fallback_order(provider):
            candidate_info = self.PROVIDERS[candidate]
            candidate_key = os.environ.get(candidate_info["env_key"], "").strip()
            attempted.append(candidate)
            try:
                async for token in self._stream_with_provider(candidate, candidate_key, messages, temperature, max_tokens):
                    yield token
                return
            except Exception as e:
                logger.error(f"Cloud model error ({candidate}): {e}", exc_info=True)

        attempted_labels = ", ".join(self.PROVIDERS[pid]["label"] for pid in attempted) or info["label"]
        yield f"\n\nSorry, the configured cloud model providers are unavailable right now ({attempted_labels}). Please try again later or switch to the Core model."

    async def _stream_openai(self, api_key, messages, temperature, max_tokens):
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise Exception(f"OpenAI API error {resp.status_code}: {error_body.decode()[:200]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            yield token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def _stream_gemini(self, api_key, messages, temperature, max_tokens):
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key={api_key}"
        # Convert OpenAI-style messages to Gemini format
        system_text = ""
        contents = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            elif m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise Exception(f"Gemini API error {resp.status_code}: {error_body.decode()[:200]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def _stream_anthropic(self, api_key, messages, temperature, max_tokens):
        import httpx
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # Separate system from messages for Anthropic
        system_text = ""
        conv_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                conv_messages.append({"role": m["role"], "content": m["content"]})
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_text,
            "messages": conv_messages,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise Exception(f"Anthropic API error {resp.status_code}: {error_body.decode()[:200]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        if chunk.get("type") == "content_block_delta":
                            text = chunk.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def _stream_groq(self, api_key, messages, temperature, max_tokens):
        """Stream from Groq using OpenAI-compatible API."""
        import httpx
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-70b-versatile",  # Current Groq model (Llama 3.1 70B)
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise Exception(f"Groq API error {resp.status_code}: {error_body.decode()[:200]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            yield token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


if __name__ == "__main__":
    # Test the LLM engine
    import asyncio
    
    async def test():
        engine = MedicalLLMEngine()
        await engine.initialize()
        
        # Test response
        result = await engine.generate_response(
            message="I have a headache",
            history=[],
            patient_id="test_patient"
        )
        
        print(f"Response: {result['response']}")
        print(f"Confidence: {result['confidence']}")
    
    asyncio.run(test())

