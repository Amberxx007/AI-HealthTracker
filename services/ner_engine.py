"""
Biomedical NER Engine
Uses scispaCy (en_ner_bc5cdr_md) for Named Entity Recognition on medical text.
Detects diseases, chemicals (drugs), and lab-related entities from OCR/PDF text.

Models used:
  - en_ner_bc5cdr_md  → DISEASE + CHEMICAL entities (BC5CDR corpus)
  - en_core_sci_sm    → General biomedical entities (fallback)
"""

import re
from typing import Dict, List, Optional, Tuple
from utils.utils_logger import setup_logger

logger = setup_logger(__name__)

# Lazy-loaded models
_ner_model = None
_sci_model = None


def _get_ner_model():
    """Load BC5CDR NER model (diseases + chemicals)"""
    global _ner_model
    if _ner_model is None:
        import spacy
        logger.info("Loading scispaCy NER model: en_ner_bc5cdr_md ...")
        _ner_model = spacy.load("en_ner_bc5cdr_md")
        logger.info("scispaCy NER model loaded")
    return _ner_model


def _get_sci_model():
    """Load general biomedical model for broader entity detection"""
    global _sci_model
    if _sci_model is None:
        import spacy
        try:
            logger.info("Loading scispaCy model: en_core_sci_sm ...")
            _sci_model = spacy.load("en_core_sci_sm")
            logger.info("scispaCy en_core_sci_sm loaded")
        except OSError:
            logger.warning("en_core_sci_sm not available, using NER model only")
            _sci_model = _get_ner_model()
    return _sci_model


# ── Normalization helpers ──

# Common medical abbreviation → canonical name
_DISEASE_ALIASES = {
    "dm": "diabetes mellitus",
    "dm2": "type 2 diabetes mellitus",
    "t2dm": "type 2 diabetes mellitus",
    "t1dm": "type 1 diabetes mellitus",
    "htn": "hypertension",
    "bp": "hypertension",
    "ckd": "chronic kidney disease",
    "copd": "chronic obstructive pulmonary disease",
    "cad": "coronary artery disease",
    "mi": "myocardial infarction",
    "chf": "congestive heart failure",
    "af": "atrial fibrillation",
    "afib": "atrial fibrillation",
    "uti": "urinary tract infection",
    "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism",
    "tb": "tuberculosis",
    "ra": "rheumatoid arthritis",
    "sle": "systemic lupus erythematosus",
    "oa": "osteoarthritis",
    "gerd": "gastroesophageal reflux disease",
    "ibs": "irritable bowel syndrome",
    "mg": "myasthenia gravis",
    "ms": "multiple sclerosis",
    "pcos": "polycystic ovary syndrome",
    "osa": "obstructive sleep apnea",
}

_DRUG_ALIASES = {
    "asa": "aspirin",
    "pcm": "paracetamol",
    "apap": "acetaminophen",
    "mtx": "methotrexate",
    "hctz": "hydrochlorothiazide",
}

# Lab analytes the NER model may tag as CHEMICAL — filter these from drug lists
_LAB_ANALYTES = {
    "glucose", "creatinine", "hemoglobin", "haemoglobin", "albumin", "globulin",
    "bilirubin", "cholesterol", "triglycerides", "urea", "calcium",
    "potassium", "sodium", "chloride", "phosphorus", "magnesium", "iron",
    "ferritin", "uric acid", "protein", "hba1c", "troponin",
    "creatine", "amylase", "lipase", "lactate", "bicarbonate",
}

# Value + unit patterns for extracting measurements near entities
_MEASUREMENT_RE = re.compile(
    r'(\d+\.?\d*)\s*(mg/dL|g/dL|mmol/L|mIU/L|ng/mL|pg/mL|µg/dL|IU/mL|U/L|%|mm/hr|fL|pg|×10[³³]/µL)',
    re.IGNORECASE,
)


class NEREngine:
    """Extract biomedical entities (diseases, drugs, measurements) from text."""

    def __init__(self):
        self._initialized = False
        logger.info("NER Engine initialized (lazy load)")

    async def initialize(self):
        """Pre-load models during app startup."""
        try:
            _get_ner_model()
            self._initialized = True
        except Exception as e:
            logger.warning(f"NER init failed (will retry on use): {e}")

    def extract_entities(self, text: str) -> Dict:
        """
        Full NER pipeline on raw text (OCR output, chat message, etc.).

        Returns:
            {
                "diseases": [{"text": "diabetes mellitus", "label": "DISEASE", "start": 10, "end": 29}],
                "chemicals": [{"text": "metformin", "label": "CHEMICAL", "start": 50, "end": 59}],
                "measurements": [{"value": "10.2", "unit": "g/dL", "start": 70, "end": 80}],
                "entity_count": 5,
            }
        """
        nlp = _get_ner_model()
        doc = nlp(text)

        diseases = []
        chemicals = []
        seen_diseases = set()
        seen_chemicals = set()

        for ent in doc.ents:
            ent_lower = ent.text.lower().strip()
            if len(ent_lower) < 2:
                continue

            if ent.label_ == "DISEASE":
                normalized = _DISEASE_ALIASES.get(ent_lower, ent.text.strip())
                key = normalized.lower()
                if key not in seen_diseases:
                    seen_diseases.add(key)
                    diseases.append({
                        "text": normalized,
                        "label": "DISEASE",
                        "start": ent.start_char,
                        "end": ent.end_char,
                    })

            elif ent.label_ == "CHEMICAL":
                # Skip lab analytes (glucose, creatinine, etc.) — not medications
                if ent_lower in _LAB_ANALYTES:
                    continue
                normalized = _DRUG_ALIASES.get(ent_lower, ent.text.strip())
                key = normalized.lower()
                if key not in seen_chemicals:
                    seen_chemicals.add(key)
                    chemicals.append({
                        "text": normalized,
                        "label": "CHEMICAL",
                        "start": ent.start_char,
                        "end": ent.end_char,
                    })

        # Also extract measurements (value + unit) via regex
        measurements = []
        for m in _MEASUREMENT_RE.finditer(text):
            measurements.append({
                "value": m.group(1),
                "unit": m.group(2),
                "start": m.start(),
                "end": m.end(),
            })

        return {
            "diseases": diseases,
            "chemicals": chemicals,
            "measurements": measurements,
            "entity_count": len(diseases) + len(chemicals) + len(measurements),
        }

    def extract_diseases(self, text: str) -> List[str]:
        """Quick extraction: return list of disease names found in text."""
        result = self.extract_entities(text)
        return [d["text"] for d in result["diseases"]]

    def extract_drugs(self, text: str) -> List[str]:
        """Quick extraction: return list of drug/chemical names found in text."""
        result = self.extract_entities(text)
        return [c["text"] for c in result["chemicals"]]

    def enrich_ocr_results(self, raw_text: str, lab_results: List[Dict]) -> Dict:
        """
        Run NER on OCR text and merge findings with regex-extracted lab results.
        
        Returns enriched data with:
          - Original lab_results (from regex)
          - NER-detected diseases (may reveal diagnoses from report headers)
          - NER-detected drugs (medications mentioned in reports)
          - Any measurements NER found that regex missed
        """
        ner_data = self.extract_entities(raw_text)

        # Find existing test names from regex
        existing_tests = {lr["test_name"] for lr in lab_results}

        return {
            "lab_results": lab_results,
            "ner_diseases": ner_data["diseases"],
            "ner_drugs": ner_data["chemicals"],
            "ner_measurements": ner_data["measurements"],
            "ner_entity_count": ner_data["entity_count"],
            "regex_count": len(lab_results),
            "method": "regex+ner",
        }

    def analyze_chat_message(self, message: str) -> Dict:
        """
        Extract medical entities from a chat message for context enrichment.
        
        Useful for: understanding what conditions/drugs the patient mentions
        to provide the LLM with structured context.
        """
        ner_data = self.extract_entities(message)

        return {
            "mentioned_conditions": [d["text"] for d in ner_data["diseases"]],
            "mentioned_medications": [c["text"] for c in ner_data["chemicals"]],
            "has_medical_content": ner_data["entity_count"] > 0,
        }

    def check_health(self) -> bool:
        return self._initialized
