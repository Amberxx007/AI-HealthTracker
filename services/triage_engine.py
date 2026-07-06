"""
Symptom Triage Engine
Rule-based clinical risk classification (offline)
Classifies patient symptoms into: emergency, urgent, moderate, low
"""

import re
from typing import Dict, List, Tuple
from utils.utils_logger import setup_logger

logger = setup_logger(__name__)


class TriageEngine:
    """
    Offline symptom triage with multilingual keyword matching.
    Returns risk level + reasoning for the LLM to use.
    """

    # ── Emergency (call 911) ────────────────────────────────────
    EMERGENCY_PATTERNS = [
        # Cardiac
        (r"chest\s*pain.*sweat|heart\s*attack|cardiac\s*arrest", "Possible cardiac emergency"),
        (r"crushing.*chest|pressure.*chest.*arm", "Possible heart attack"),
        # Respiratory
        (r"can.?t\s*breathe|cannot\s*breathe|choking|suffocating", "Respiratory emergency"),
        (r"breathing\s*stopped|not\s*breathing|blue\s*lips", "Respiratory arrest"),
        # Neurological
        (r"stroke|face\s*droop|slurred\s*speech.*sudden", "Possible stroke"),
        (r"seizure.*won.?t\s*stop|status\s*epilepticus", "Prolonged seizure"),
        (r"unconscious|unresponsive|passed\s*out.*won.?t\s*wake", "Loss of consciousness"),
        # Trauma
        (r"severe\s*bleeding.*won.?t\s*stop|hemorrhag", "Severe hemorrhage"),
        (r"severe\s*head\s*injury|skull\s*fracture", "Head trauma"),
        # Mental Health
        (r"suicid|kill\s*myself|want\s*to\s*die|end\s*my\s*life", "Suicide risk"),
        # Anaphylaxis
        (r"throat.*swell.*can.?t.*breathe|anaphyla", "Anaphylaxis"),
        # Hindi
        (r"सीने\s*में\s*दर्द|दिल\s*का\s*दौरा|सांस\s*नहीं", "Cardiac/respiratory emergency"),
        (r"बेहोश|आत्महत्या|मर\s*जाना", "Emergency detected"),
        # Punjabi
        (r"ਛਾਤੀ\s*ਵਿੱਚ\s*ਦਰਦ|ਦਿਲ\s*ਦਾ\s*ਦੌਰਾ|ਸਾਹ\s*ਨਹੀਂ", "Cardiac/respiratory emergency"),
        (r"ਬੇਹੋਸ਼|ਬਹੁਤ\s*ਤੇਜ਼\s*ਦਰਦ", "Emergency detected"),
    ]

    # ── Urgent (see doctor within 24h) ──────────────────────────
    URGENT_PATTERNS = [
        (r"high\s*fever.*stiff\s*neck|meningitis", "Possible meningitis"),
        (r"fever.*above\s*10[3-5]|fever.*39\.\d|fever.*40", "Very high fever"),
        (r"vomiting\s*blood|blood\s*in\s*vomit|hematemesis", "GI bleeding"),
        (r"blood\s*in\s*stool|black.*tarry.*stool|melena", "GI bleeding"),
        (r"severe\s*abdominal\s*pain|appendicitis", "Acute abdomen"),
        (r"sudden.*worst.*headache|thunderclap\s*headache", "Possible SAH"),
        (r"sudden.*vision\s*loss|sudden.*blind", "Acute vision loss"),
        (r"severe\s*allergic|angioedem", "Severe allergy"),
        (r"broken\s*bone|fracture.*deform", "Suspected fracture"),
        # Danger signs — elderly
        (r"(?:elderly|old|aged|senior|grandm|grandp|nani|nana|dadi|dada).*(?:confus|fall|faint|dizz|weak)", "Danger sign in elderly — confusion/fall/weakness"),
        (r"(?:confus|disoriented|not\s*recogni).*(?:elder|old|age\s*[6-9]\d|age\s*[7-9])", "Acute confusion in elderly"),
        (r"sudden.*(?:confus|disoriented|can.?t\s*remember)", "Sudden confusion — possible stroke/infection"),
        (r"fall.*(?:elder|old|hit\s*head|can.?t\s*get\s*up)", "Fall in elderly — injury risk"),
        # Danger signs — general
        (r"worst.*pain.*(?:ever|life)|(?:10|ten)\s*(?:out\s*of|\/)\s*10\s*pain", "Worst-ever pain — danger sign"),
        (r"cough.*blood|blood.*cough|hemoptysis", "Coughing blood"),
        (r"swollen.*leg.*(?:one|single|left|right)|(?:one|single)\s*leg.*swollen", "Unilateral leg swelling — possible DVT"),
        (r"sudden.*swelling.*(?:face|throat|tongue|lip)", "Sudden facial/throat swelling"),
        (r"(?:bp|blood\s*pressure).*(?:1[89]\d|2[0-9]\d)\s*\/\s*(?:1[1-9]\d|[2-9]\d\d)", "Dangerously high blood pressure"),
        (r"sugar.*(?:above|over|more)\s*(?:3[0-9]\d|4\d\d|5\d\d)|(?:3[0-9]\d|4\d\d|5\d\d)\s*(?:mg|sugar|glucose)", "Very high blood sugar"),
        (r"बहुत\s*तेज\s*बुखार|खून\s*की\s*उल्टी", "Urgent medical need"),
    ]

    # ── Moderate (see doctor within days) ───────────────────────
    MODERATE_PATTERNS = [
        (r"fever.*[3-7]\s*days|persistent\s*fever", "Persistent fever"),
        (r"blood\s*in\s*urine|hematuria", "Blood in urine"),
        (r"chest\s*pain.*mild|chest\s*discomfort", "Chest discomfort"),
        (r"shortness.*breath.*exertion|breathless.*stair", "Exertional dyspnea"),
        (r"lump|mass|growth|swelling.*hard", "New lump/mass"),
        (r"weight\s*loss.*unexplained|losing\s*weight.*no\s*reason", "Unexplained weight loss"),
        (r"numbness.*tingling.*persist|weakness.*one\s*side", "Neurological symptom"),
        (r"recurrent.*infection|frequent.*infection", "Recurrent infections"),
    ]

    def __init__(self):
        self._compile_patterns()
        logger.info("Triage Engine initialized")

    def _compile_patterns(self):
        self._emergency = [(re.compile(p, re.IGNORECASE), reason) for p, reason in self.EMERGENCY_PATTERNS]
        self._urgent = [(re.compile(p, re.IGNORECASE), reason) for p, reason in self.URGENT_PATTERNS]
        self._moderate = [(re.compile(p, re.IGNORECASE), reason) for p, reason in self.MODERATE_PATTERNS]

    def assess(self, text: str) -> Dict:
        """
        Assess risk level from patient text.
        Returns: {level, reason, recommendation}
        """
        # Check emergency
        for pattern, reason in self._emergency:
            if pattern.search(text):
                return {
                    "level": "emergency",
                    "reason": reason,
                    "recommendation": "Call emergency services (911) immediately. Do not wait.",
                    "color": "red"
                }

        # Check urgent
        for pattern, reason in self._urgent:
            if pattern.search(text):
                return {
                    "level": "urgent",
                    "reason": reason,
                    "recommendation": "Seek medical attention within 24 hours. Visit urgent care or emergency room.",
                    "color": "orange"
                }

        # Check moderate
        for pattern, reason in self._moderate:
            if pattern.search(text):
                return {
                    "level": "moderate",
                    "reason": reason,
                    "recommendation": "Schedule a doctor appointment within the next few days.",
                    "color": "yellow"
                }

        # Default: general / low risk
        return {
            "level": "general",
            "reason": "General health inquiry",
            "recommendation": "Home care may be appropriate. Monitor symptoms.",
            "color": "green"
        }

    def get_triage_prompt(self, triage_result: Dict) -> str:
        """Build triage context for LLM prompt"""
        level = triage_result["level"]
        reason = triage_result["reason"]

        if level == "emergency":
            return f"""⚠️ TRIAGE ALERT: EMERGENCY — {reason}
You MUST immediately advise the patient to call emergency services.
Provide first-aid guidance while waiting for help.
Do NOT engage in extended conversation — priority is getting them emergency care."""

        if level == "urgent":
            return f"""⚠️ TRIAGE ALERT: URGENT — {reason}
This is a DANGER SIGN. Advise the patient to seek medical attention within 24 hours.
Start your response by flagging this danger sign prominently.
Explain why this needs prompt professional evaluation.
Provide at least 2 differential diagnoses with single-line reasoning.
Provide supportive care advice while they arrange to see a doctor."""

        if level == "moderate":
            return f"""TRIAGE: MODERATE CONCERN — {reason}
The patient should schedule a doctor visit soon.
Provide differential diagnoses with classification/staging where applicable.
Provide helpful information, home care suggestions, and explain when to escalate to urgent care."""

        return "TRIAGE: GENERAL INQUIRY — Standard health question. Provide thorough, helpful medical information with differential diagnoses if it's a health complaint."

    def check_health(self) -> bool:
        return True
