"""
Medical Report OCR Engine
Parses lab reports using EasyOCR (offline) + PyMuPDF for PDFs.
Extracts structured values from multi-line and inline formats.
"""

import os
import re
import tempfile
from typing import Dict, List, Optional
from utils.utils_logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)


_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (first load downloads ~100MB)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("EasyOCR ready")
    return _reader


# Comprehensive lab test patterns
LAB_PATTERNS = {
    # CBC / Hematology
    "hemoglobin": { "aliases": [r"h[ae]moglobin\b", r"\bhb\b", r"\bhgb\b"], "unit": "g/dL", "normal": "12.0-17.5" },
    "wbc": { "aliases": [r"\bwbc\b", r"white\s*blood\s*cell", r"total\s*leucocyte\s*count", r"\btlc\b"], "unit": "×10³/μL", "normal": "4.5-11.0" },
    "rbc_count": { "aliases": [r"rbc\s*count", r"red\s*blood\s*cell\s*count", r"erythrocyte\s*count"], "unit": "10^6/µL", "normal": "3.8-5.5" },
    "platelet": { "aliases": [r"platelet", r"\bplt\b", r"thrombocyte"], "unit": "×10³/μL", "normal": "150-400" },
    "pcv": { "aliases": [r"\bpcv\b", r"packed\s*cell\s*vol", r"hematocrit", r"\bhct\b"], "unit": "%", "normal": "36-46" },
    "mcv": { "aliases": [r"\bmcv\b", r"\bmc\s*v\b", r"mean\s*corpuscular\s*vol"], "unit": "fL", "normal": "83-101" },
    "mch": { "aliases": [r"\bmch\b(?!\s*c)", r"\bmc\s*h\b(?!\s*c)", r"mean\s*corpuscular\s*h[ae]mo(?!.*conc)"], "unit": "pg", "normal": "27-32" },
    "mchc": { "aliases": [r"\bmchc\b", r"mean\s*corpuscular\s*h[ae]mo.*conc"], "unit": "g/dL", "normal": "31.5-34.5" },
    "rdw_cv": { "aliases": [r"rdw\s*[\(\[]?\s*cv", r"rdw\s*$"], "unit": "%", "normal": "11.6-14.0" },
    "esr": { "aliases": [r"\besr\b", r"erythrocyte\s*sedimentation"], "unit": "mm/hr", "normal": "0-20" },
    "neutrophil": { "aliases": [r"neutrophil"], "unit": "%", "normal": "40-80" },
    "lymphocyte": { "aliases": [r"lymphocyte"], "unit": "%", "normal": "20-40" },
    "monocyte": { "aliases": [r"monocyte"], "unit": "%", "normal": "2-10" },
    "eosinophil": { "aliases": [r"eosinophil"], "unit": "%", "normal": "1-6" },
    "basophil": { "aliases": [r"basophil"], "unit": "%", "normal": "0-2" },
    # Sugar
    "glucose_fasting": { "aliases": [r"fasting.*glucose", r"\bfbs\b", r"fasting.*sugar", r"glucose.*fasting"], "unit": "mg/dL", "normal": "70-100" },
    "glucose_random": { "aliases": [r"glucose\s*random", r"\brbs\b", r"random.*glucose", r"blood\s*sugar\s*random", r"sugar\s*random"], "unit": "mg/dL", "normal": "70-140" },
    "glucose_pp": { "aliases": [r"post\s*prandial", r"\bppbs\b", r"glucose.*pp"], "unit": "mg/dL", "normal": "70-140" },
    "hba1c": { "aliases": [r"hba1c", r"hbaic", r"glycated\s*h[ae]mo", r"\ba1c\b", r"glycosylated"], "unit": "%", "normal": "4.0-5.6" },
    # Lipid Profile
    "cholesterol_total": { "aliases": [r"total\s*cholesterol", r"cholesterol\s*total", r"t[.-]?chol"], "unit": "mg/dL", "normal": "<200" },
    "hdl": { "aliases": [r"\bhdl\b", r"hd\s*l\s*cholesterol", r"high\s*density"], "unit": "mg/dL", "normal": ">40" },
    "ldl": { "aliases": [r"\bldl\b", r"ld\s*l\s*cholesterol\b(?!.*ratio)", r"low\s*density"], "unit": "mg/dL", "normal": "<100" },
    "vldl": { "aliases": [r"\bvldl\b", r"very\s*low\s*density"], "unit": "mg/dL", "normal": "<30" },
    "triglycerides": { "aliases": [r"triglyceride", r"\btg\b"], "unit": "mg/dL", "normal": "<150" },
    # Liver (LFT)
    "bilirubin_total": { "aliases": [r"bilirubin\s*total", r"total\s*bilirubin", r"t[.-]?\s*bil"], "unit": "mg/dL", "normal": "0.2-1.2" },
    "bilirubin_direct": { "aliases": [r"bilirubin\s*direct", r"direct\s*bilirubin", r"d[.-]?\s*bil"], "unit": "mg/dL", "normal": "0.0-0.5" },
    "bilirubin_indirect": { "aliases": [r"bilirubin\s*indirect", r"indirect\s*bilirubin"], "unit": "mg/dL", "normal": "0.1-1.0" },
    "sgpt": { "aliases": [r"sgpt", r"\balt\b", r"alanine\s*amino"], "unit": "U/L", "normal": "0-55" },
    "sgot": { "aliases": [r"sgot", r"\bast\b", r"aspartate\s*amino"], "unit": "U/L", "normal": "5-34" },
    "alkaline_phosphatase": { "aliases": [r"alkaline\s*phosphatase", r"\balp\b"], "unit": "U/L", "normal": "40-150" },
    "total_protein": { "aliases": [r"total\s*protein"], "unit": "g/dL", "normal": "6.4-8.3" },
    "albumin": { "aliases": [r"\balbumin\b(?!.*glob)(?!.*creat)(?!.*urine)"], "unit": "g/dL", "normal": "3.8-5.0" },
    "globulin": { "aliases": [r"\bglobulin\b(?!.*album)"], "unit": "g/dL", "normal": "2.3-3.5" },
    "ag_ratio": { "aliases": [r"albumin\s*[:/]\s*globulin\s*ratio", r"a\s*[:/]\s*g\s*ratio"], "unit": "", "normal": "1.0-2.1" },
    "ggt": { "aliases": [r"gamma\s*glutamyl", r"\bggt\b"], "unit": "U/L", "normal": "9-36" },
    # Kidney (KFT)
    "blood_urea": { "aliases": [r"blood\s*urea(?!\s*nitrogen)", r"^urea\b"], "unit": "mg/dL", "normal": "19-44" },
    "bun": { "aliases": [r"\bbun\b", r"blood\s*urea\s*nitrogen"], "unit": "mg/dL", "normal": "7-18.7" },
    "creatinine": { "aliases": [r"\bcreatinine\b(?!.*ratio)(?!.*clearance)"], "unit": "mg/dL", "normal": "0.5-1.3" },
    "egfr": { "aliases": [r"\begfr\b", r"glomerular\s*filtration"], "unit": "mL/min", "normal": ">90" },
    "uric_acid": { "aliases": [r"uric\s*acid"], "unit": "mg/dL", "normal": "2.5-7.2" },
    "calcium": { "aliases": [r"calcium\s*serum", r"serum\s*calcium", r"\bcalcium\b(?!.*urine)"], "unit": "mg/dL", "normal": "8.4-10.5" },
    "phosphorus": { "aliases": [r"\bphosphorus\b", r"phosphate\b"], "unit": "mg/dL", "normal": "2.5-4.5" },
    "sodium": { "aliases": [r"\bsodium\b"], "unit": "mmol/L", "normal": "136-145" },
    "potassium": { "aliases": [r"\bpotassium\b"], "unit": "mmol/L", "normal": "3.5-5.1" },
    "chloride": { "aliases": [r"\bchloride\b"], "unit": "mmol/L", "normal": "98-107" },
    # Thyroid
    "tsh": { "aliases": [r"\btsh\b", r"\btsh[a-z]*\b", r"thyroid\s*stimulat"], "unit": "mIU/L", "normal": "0.35-4.94" },
    "t3": { "aliases": [r"triiodothyronine.*?\(t3\)", r"triiodothyronine\b", r"total\s*\(t3\)", r"\bt3\b(?!\s*and)"], "unit": "ng/dL", "normal": "35-193" },
    "t4": { "aliases": [r"total\s*thyroxine", r"thyroxine.*?\(t4\)", r"total\s*\(t4\)", r"\bt4\b(?!\s*and)"], "unit": "µg/dL", "normal": "4.87-11.72" },
    # Iron
    "iron": { "aliases": [r"serum\s*iron", r"\biron\b(?!.*binding)(?!.*saturation)(?!.*deficiency)"], "unit": "µg/dL", "normal": "60-170" },
    "ferritin": { "aliases": [r"\bferritin\b"], "unit": "ng/mL", "normal": "20-500" },
    "tibc": { "aliases": [r"\btibc\b", r"total\s*iron\s*binding"], "unit": "µg/dL", "normal": "250-370" },
    # Vitamins
    "vitamin_d": { "aliases": [r"vitamin\s*d\b", r"25.*hydroxy.*d", r"25\s*oh.*(?:vit|min|d\b)", r"\bvit\s*d\b"], "unit": "ng/mL", "normal": "30-100" },
    "vitamin_b12": { "aliases": [r"vitamin\s*b\s*l?\s*[12]{1,2}", r"\bb12\b", r"\bbl2\b", r"cobalamin"], "unit": "pg/mL", "normal": "200-900" },
    # HbA2 / HPLC
    "hba2": { "aliases": [r"h[ae]moglobin\s*a2", r"\bhba2\b"], "unit": "%", "normal": "1.5-3.7" },
    "hb_f": { "aliases": [r"foetal\s*h[ae]mo", r"fetal\s*h[ae]mo", r"\bhbf\b"], "unit": "%", "normal": "0-2" },
    # BP — only match if explicitly labeled
    "bp_systolic": { "aliases": [r"systolic\s*(?:bp|blood\s*pressure)", r"bp\s*sys"], "unit": "mmHg", "normal": "<120" },
    "bp_diastolic": { "aliases": [r"diastolic\s*(?:bp|blood\s*pressure)", r"bp\s*dia"], "unit": "mmHg", "normal": "<80" },
    # Inflammation
    "crp": { "aliases": [r"\bcrp\b", r"c\s*reactive\s*protein"], "unit": "mg/L", "normal": "<6.0" },
    "mean_plasma_glucose": { "aliases": [r"estimated\s*average\s*glucose"], "unit": "mg/dL", "normal": "90-120" },
    # Urine — numeric
    "urine_ph": { "aliases": [r"reaction\s*\(?ph\)?", r"urine\s*ph", r"\bph\b(?=.*urine|.*4\.5)"], "unit": "", "normal": "4.5-8.0" },
    "urine_specific_gravity": { "aliases": [r"specific\s*gravity"], "unit": "", "normal": "1.010-1.030" },
    "urine_pus_cells": { "aliases": [r"pus\s*cells?\s*\(?wbc", r"pus\s*cells"], "unit": "/hpf", "normal": "0-5" },
    "urine_epithelial": { "aliases": [r"epithelial\s*cells?"], "unit": "/hpf", "normal": "0-4" },
    # Platelet indices
    "mpv": { "aliases": [r"\bmpv\b", r"mean\s*platelet\s*vol"], "unit": "fL", "normal": "9.3-12.1" },
    "pct": { "aliases": [r"\bpct\b(?!.*procalcitonin)", r"plateletcrit"], "unit": "%", "normal": "0.17-0.32" },
    "pdw": { "aliases": [r"\bpdw\b", r"platelet\s*distribution\s*width"], "unit": "fL", "normal": "8.3-25.0" },
    # Additional CBC
    "reticulocyte": { "aliases": [r"reticulocyte\s*count", r"\breticulocyte\b"], "unit": "%", "normal": "0.5-2.5" },
    "immature_granulocyte": { "aliases": [r"immature\s*granulocyte"], "unit": "%", "normal": "0-0.5" },
    # Additional
    "ldh": { "aliases": [r"\bldh\b", r"lactate\s*dehydrogenase"], "unit": "U/L", "normal": "125-220" },
    "cpk": { "aliases": [r"\bcpk\b", r"creatine\s*phosphokinase", r"creatine\s*kinase"], "unit": "U/L", "normal": "26-192" },
    "amylase": { "aliases": [r"\bamylase\b"], "unit": "U/L", "normal": "28-100" },
    "lipase": { "aliases": [r"\blipase\b"], "unit": "U/L", "normal": "0-67" },
    "magnesium": { "aliases": [r"\bmagnesium\b"], "unit": "mg/dL", "normal": "1.8-2.6" },
    "procalcitonin": { "aliases": [r"procalcitonin"], "unit": "ng/mL", "normal": "<0.5" },
    # Infection markers (qualitative)
    "rubella_igg": { "aliases": [r"rubella.*igg", r"rubella.*\(german.*\).*igg"], "unit": "IU/mL", "normal": ">10" },
    "rubella_igm": { "aliases": [r"rubella.*igm"], "unit": "AU/mL", "normal": "<5" },
}

# Qualitative tests — stored as status text, not numeric
QUALITATIVE_PATTERNS = {
    "urine_glucose": { "aliases": [r"urine\s*glucose\s*\(?sugar\)?", r"urine\s*glucose"], "normal": "Negative" },
    "urine_protein": { "aliases": [r"urine\s*protein\s*\(?albumin\)?", r"urine\s*protein"], "normal": "Negative" },
    "urine_ketones": { "aliases": [r"urine\s*ketones?\s*\(?acetone\)?", r"urine\s*ketone"], "normal": "Negative" },
    "urine_blood": { "aliases": [r"(?:blood|occult\s*blood)\s*$", r"peroxidase\s*hemoglobin"], "normal": "Negative" },
    "urine_bilirubin": { "aliases": [r"bilirubin\s*urine"], "normal": "Negative" },
    "urine_nitrite": { "aliases": [r"\bnitrite\b"], "normal": "Negative" },
    "urine_urobilinogen": { "aliases": [r"urobilinogen"], "normal": "Normal" },
    "urine_leucocyte_esterase": { "aliases": [r"leucocyte\s*esterase"], "normal": "Negative" },
    "hiv_antibody": { "aliases": [r"hiv\s*1\s*&?\s*2\s*antibod", r"hiv\s*antibod"], "normal": "Non Reactive" },
    "hepatitis_b": { "aliases": [r"hepatitis\s*b\s*surface\s*antigen", r"\bhbsag\b"], "normal": "Non Reactive" },
    "hepatitis_c": { "aliases": [r"hepatitis\s*c\s*antibod", r"\bhcv\b(?!.*viral\s*load)", r"anti[\s-]hcv"], "normal": "Non Reactive" },
    "vdrl": { "aliases": [r"\bvdrl\b", r"\brpr\b", r"syphilis"], "normal": "Non Reactive" },
    # Microscopic
    "urine_rbc": { "aliases": [r"red\s*blood\s*cells?"], "normal": "Absent" },
    "urine_crystals": { "aliases": [r"\bcrystals?\b"], "normal": "Absent" },
    "urine_cast": { "aliases": [r"\bcast\b(?!.*iron)"], "normal": "Absent" },
    "urine_yeast": { "aliases": [r"yeast\s*cells?"], "normal": "Absent" },
    "urine_amorphous": { "aliases": [r"amorphous\s*deposits?"], "normal": "Absent" },
    "urine_bacteria": { "aliases": [r"\bbacteria\b"], "normal": "Absent" },
}

# Descriptive tests — free-form text values (colour, appearance, blood group)
DESCRIPTIVE_PATTERNS = {
    "urine_colour": { "aliases": [r"\bcolou?r\b(?!.*excahnge|.*base|.*indicator)"], "normal": "Pale yellow" },
    "urine_transparency": { "aliases": [r"\btransparency\b"], "normal": "Clear" },
    "urine_deposit": { "aliases": [r"\bdeposit\b"], "normal": "Absent" },
    "blood_group": { "aliases": [r"^blood\s*group$"], "normal": "" },
    "rh_factor": { "aliases": [r"^rh\s*factor$"], "normal": "" },
    "urine_volume": { "aliases": [r"\bvolume\b"], "normal": "" },
}

# Known descriptive values for matching
_descriptive_values_re = re.compile(
    r"^(Pale\s*yellow|Yellow|Dark\s*yellow|Straw|Amber|Red|Brown|Orange|Colorless|Clear|Slightly?\s*Turbid|Turbid|Hazy|Absent|Present|Few|Many|Moderate|Plenty|\d+|A[B]?|B|O|AB|Positive|Negative)\s*$",
    re.IGNORECASE,
)

# Compile patterns once
_compiled = {}
for test_name, info in LAB_PATTERNS.items():
    _compiled[test_name] = {
        "patterns": [re.compile(alias, re.IGNORECASE) for alias in info["aliases"]],
        "unit": info["unit"],
        "normal": info["normal"],
    }

_compiled_qual = {}
for test_name, info in QUALITATIVE_PATTERNS.items():
    _compiled_qual[test_name] = {
        "patterns": [re.compile(alias, re.IGNORECASE) for alias in info["aliases"]],
        "normal": info["normal"],
    }

_compiled_desc = {}
for test_name, info in DESCRIPTIVE_PATTERNS.items():
    _compiled_desc[test_name] = {
        "patterns": [re.compile(alias, re.IGNORECASE) for alias in info["aliases"]],
        "normal": info["normal"],
    }

# Qualitative value regex — matches Positive, Negative, Reactive, Non-Reactive, etc.
_qual_re = re.compile(
    r"(NON[\s-]*REACTIVE|REACTIVE|POSITIVE\s*\([^)]*\)|POSITIVE|NEGATIVE|ABSENT|PRESENT|NORMAL|TRACE|DETECTED|NOT\s*DETECTED)",
    re.IGNORECASE,
)

# Generic number extraction near a test name (handles comma-separated like 2,23,000 or 7,500)
_value_re = re.compile(r"[\s:=]+(\d[\d,]*\.?\d*)")
# BP: must have "bp" or "blood pressure" context nearby, not just any X/Y number
_bp_re = re.compile(r"(?:bp|blood\s*pressure)[^\n]{0,20}(\d{2,3})\s*/\s*(\d{2,3})", re.IGNORECASE)

def _clean_number(s: str) -> str:
    """Remove commas from OCR'd numbers: '2,23,000' -> '223000', '7,500' -> '7500'"""
    return s.replace(',', '')


class OCREngine:
    """Extract lab values from report images and PDFs"""

    def __init__(self):
        self._reader = None
        logger.info("OCR Engine initialized (lazy load)")

    async def initialize(self):
        try:
            _get_reader()
        except Exception as e:
            logger.warning(f"OCR init failed (will retry on use): {e}")

    def extract_text(self, image_bytes: bytes) -> str:
        """OCR an image or extract text from PDF with local model and Gemini fallback"""
        is_pdf = image_bytes[:5] == b'%PDF-'

        if is_pdf:
            # 1. Try direct PyMuPDF text extraction
            try:
                res = self._extract_text_from_pdf(image_bytes)
                if res and len(res.strip()) > 50:
                    return res
            except Exception as e:
                logger.warning(f"Local direct PDF text extraction failed: {e}")

            # 2. Try rendering PDF pages locally and OCRing them
            try:
                res = self._extract_pdf_pages_local(image_bytes)
                if res and len(res.strip()) > 50:
                    return res
            except Exception as e:
                logger.warning(f"Local PDF render + OCR failed: {e}")
        else:
            # Regular Image — try local EasyOCR
            try:
                res = self._extract_image_local(image_bytes)
                if res and len(res.strip()) > 5:
                    return res
            except Exception as e:
                logger.warning(f"Local Image EasyOCR failed: {e}")

        # 3. Fallback: Gemini OCR API
        logger.info("Using Gemini OCR fallback...")
        gemini_text = self._extract_text_via_gemini(image_bytes)
        if gemini_text:
            return gemini_text

        if is_pdf:
            return "PDF could not be processed. Please upload images of each page."
        return "Unable to analyze image. Please describe what you see."

    def _extract_image_local(self, image_bytes: bytes) -> str:
        """Process image locally with EasyOCR"""
        reader = _get_reader()
        try:
            from PIL import Image, ImageEnhance
            import io
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            w, h = img.size
            if w < 1000 or h < 1000:
                scale = max(1000 / w, 1000 / h, 1)
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=95)
            image_bytes = buf.getvalue()
        except Exception as e:
            logger.warning(f"Local image preprocessing failed: {e}")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            results = reader.readtext(tmp_path, detail=0, paragraph=True)
            return "\n".join(results)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using PyMuPDF"""
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                all_text.append(text)
        doc.close()
        combined = "\n".join(all_text)
        if len(combined.strip()) > 50:
            logger.info(f"PDF text extracted via PyMuPDF: {len(combined)} chars from {len(all_text)} pages")
            return combined
        return ""

    def _extract_pdf_pages_local(self, pdf_bytes: bytes) -> str:
        """Render pages locally and OCR with EasyOCR"""
        import fitz
        from PIL import Image, ImageEnhance
        import io
        reader = _get_reader()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text = []
        page_count = min(len(doc), 25)
        for i in range(page_count):
            page = doc[i]
            # Render at high DPI for better OCR
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            # Preprocess: enhance contrast and sharpness
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            # Save to temp file for EasyOCR
            tmp_path = os.path.join(tempfile.gettempdir(), f"ocr_page_{i}_{os.getpid()}.jpg")
            img.save(tmp_path, format='JPEG', quality=95)
            try:
                results = reader.readtext(tmp_path, detail=0, paragraph=True)
                all_text.extend(results)
                logger.info(f"Page {i+1}/{page_count}: {len(results)} text blocks")
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        doc.close()
        combined = "\n".join(all_text)
        logger.info(f"PDF OCR rendered {page_count} pages, got {len(all_text)} text blocks, {len(combined)} chars")
        return combined

    def _extract_text_via_gemini(self, image_bytes: bytes) -> str:
        """Send image or PDF to Gemini API to extract text"""
        import base64
        import httpx
        import json

        api_key = os.environ.get("GOOGLE_AI_API_KEY", "").strip()
        if not api_key:
            logger.warning("Gemini OCR requested but GOOGLE_AI_API_KEY is missing.")
            return ""

        is_pdf = image_bytes[:5] == b'%PDF-'
        mime_type = "application/pdf" if is_pdf else "image/jpeg"
        encoded_data = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "This is a medical lab report or document. Extract all the text from this document word-for-word. "
            "Preserve the structure, table columns, test names, values, units, and reference ranges. "
            "Do not summarize, do not add comments, just return the exact extracted text."
        )

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_data
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
        }

        model_candidates = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
        last_err = None

        with httpx.Client(timeout=120) as client:
            for model in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        parts = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        text_result = "".join(part.get("text", "") for part in parts).strip()
                        if text_result:
                            logger.info(f"Gemini OCR ({model}) successfully extracted {len(text_result)} characters")
                            return text_result
                    else:
                        logger.warning(f"Gemini OCR model {model} failed with status {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Error calling Gemini OCR model {model}: {e}")
                    last_err = e
                    continue

        if last_err:
            logger.error(f"Gemini OCR failed: {last_err}")
        return ""


    def parse_lab_report(self, text: str) -> List[Dict]:
        """Parse raw text into structured lab results.
        
        Two-pass approach:
        Pass 1 (inline): test name + value on the SAME line — preferred, works for
                          both clean PDFs and OCR'd scanned documents.
        Pass 2 (multi-line): test name on one line, value on a subsequent line —
                             only for tests not found in pass 1.
        """
        results = []
        found_tests = set()
        lines = text.split("\n")
        full_text = " ".join(lines)

        # Pre-compute how many test names appear on each line (for busy-line detection)
        line_test_counts = [0] * len(lines)
        for info in _compiled.values():
            for pattern in info["patterns"]:
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        line_test_counts[i] += 1
                        break  # count each test once per line

        # Check for BP pattern first (special format: 120/80)
        bp_match = _bp_re.search(full_text)
        if bp_match:
            sys_val, dia_val = bp_match.group(1), bp_match.group(2)
            for name, val, normal in [("bp_systolic", sys_val, "<120"), ("bp_diastolic", dia_val, "<80")]:
                results.append({
                    "test_name": name, "value": val, "unit": "mmHg",
                    "normal_range": normal, "status": self._assess_value(name, float(val)),
                })
                found_tests.add(name)

        # ── PASS 1: Inline extraction (test name + value on same line) ──
        for test_name, info in _compiled.items():
            if test_name in found_tests or test_name.startswith("bp_"):
                continue
            for pattern in info["patterns"]:
                found = False
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if not match:
                        continue
                    remainder = line[match.end():]
                    val_match = _value_re.search(remainder)
                    if val_match:
                        # Skip if "ratio" appears between test name and value
                        between = remainder[:val_match.start()].lower()
                        if 'ratio' in between:
                            continue
                        # Skip if too many words between test name and value
                        # (indicates a sentence/comment, not a test:value pair)
                        if len(between.split()) > 3:
                            continue
                        value = _clean_number(val_match.group(1))
                        try:
                            fval = float(value)
                        except ValueError:
                            continue
                        # Sanity check: try to fix OCR-missing decimals
                        fval = self._ocr_decimal_fix(test_name, fval)
                        value = str(fval) if fval != float(_clean_number(val_match.group(1))) else value
                        results.append({
                            "test_name": test_name, "value": value,
                            "unit": info["unit"], "normal_range": info["normal"],
                            "status": self._assess_value(test_name, fval),
                        })
                        found_tests.add(test_name)
                        found = True
                        break
                if found:
                    break

        # ── PASS 2: Multi-line extraction for remaining tests ──
        for test_name, info in _compiled.items():
            if test_name in found_tests or test_name.startswith("bp_"):
                continue
            for pattern in info["patterns"]:
                found = False
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if not match:
                        continue
                    # Skip busy lines (many test names on one line = garbled table)
                    if line_test_counts[i] > 3:
                        continue
                    # Look ahead up to 4 lines for a numeric value
                    for offset in range(1, 5):
                        if i + offset >= len(lines):
                            break
                        next_line = lines[i + offset].strip()
                        if not next_line or next_line.lower().startswith("interpretation"):
                            break
                        # Skip method lines (common in lab reports)
                        if re.match(r'^(VISUAL|WET MOUNT|Calculated|Electrical|colorimetric|Ion Exchange|Double Indicator|CLIA|Flow cytometry|Oxidase|Acid|Legals|Griless|Ehrlichs|Enzymatic|Coupling|Peroxidase|Qualil)', next_line, re.IGNORECASE):
                            continue
                        # Accept range like "2-4" as the first number (take first part)
                        range_match = re.match(r'^(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*$', next_line)
                        if range_match:
                            value = range_match.group(1)  # take the lower bound
                            try:
                                fval = float(value)
                            except ValueError:
                                continue
                            results.append({
                                "test_name": test_name, "value": next_line.strip(),
                                "unit": info["unit"], "normal_range": info["normal"],
                                "status": self._assess_value(test_name, fval),
                            })
                            found_tests.add(test_name)
                            found = True
                            break
                        # Accept line starting with a number (possibly with commas)
                        num_match = re.match(r'^([\d,]+\.?\d*)\s*$', next_line)
                        if not num_match:
                            # Also try: number followed by some text (unit)
                            num_match = re.match(r'^([\d,]+\.?\d*)\s+\S', next_line)
                        if num_match:
                            value = _clean_number(num_match.group(1))
                            try:
                                fval = float(value)
                            except ValueError:
                                continue
                            fval = self._ocr_decimal_fix(test_name, fval)
                            value = str(fval) if fval != float(_clean_number(num_match.group(1))) else value
                            unit = info["unit"]
                            normal = info["normal"]
                            if i + offset + 1 < len(lines):
                                unit_line = lines[i + offset + 1].strip()
                                # Skip dash-only separators and short junk
                                if unit_line and len(unit_line) < 20 and not re.match(r'^[\d\-–]+$', unit_line) and not re.match(r'^\d', unit_line):
                                    unit = unit_line
                            if i + offset + 2 < len(lines):
                                range_line = lines[i + offset + 2].strip()
                                if re.match(r'^[\d<>].*[-–].*\d', range_line):
                                    normal = range_line.split('U/L')[0].split('mg/dL')[0].split('g/dL')[0].strip() or info["normal"]
                            results.append({
                                "test_name": test_name, "value": value,
                                "unit": unit, "normal_range": normal,
                                "status": self._assess_value(test_name, fval),
                            })
                            found_tests.add(test_name)
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

        # ── PASS 3: Qualitative tests (Positive/Negative/Reactive/Non-Reactive) ──
        for test_name, info in _compiled_qual.items():
            if test_name in found_tests:
                continue
            for pattern in info["patterns"]:
                found = False
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if not match:
                        continue
                    # Check same line for qualitative value
                    remainder = line[match.end():]
                    qm = _qual_re.search(remainder)
                    if qm:
                        value = qm.group(1).strip()
                    else:
                        # Look ahead up to 4 lines
                        value = None
                        for offset in range(1, 5):
                            if i + offset >= len(lines):
                                break
                            nl = lines[i + offset].strip()
                            if not nl or nl.lower().startswith("interpretation"):
                                break
                            qm2 = _qual_re.match(nl)
                            if qm2:
                                value = qm2.group(1).strip()
                                break
                        if not value:
                            continue
                    norm = info["normal"]
                    status = "normal" if value.upper().replace(" ", "").replace("-", "") == norm.upper().replace(" ", "").replace("-", "") else "abnormal"
                    results.append({
                        "test_name": test_name, "value": value,
                        "unit": "", "normal_range": norm,
                        "status": status,
                    })
                    found_tests.add(test_name)
                    found = True
                    break
                if found:
                    break

        # ── PASS 4: Descriptive tests (colour, transparency, blood group, etc.) ──
        for test_name, info in _compiled_desc.items():
            if test_name in found_tests:
                continue
            for pattern in info["patterns"]:
                found = False
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if not match:
                        continue
                    # Check same line for descriptive value
                    remainder = line[match.end():].strip()
                    # Skip method keywords that appear on same line
                    dm = _descriptive_values_re.search(remainder)
                    if dm:
                        value = dm.group(1).strip()
                    else:
                        # Look ahead up to 4 lines, skip method lines
                        value = None
                        for offset in range(1, 5):
                            if i + offset >= len(lines):
                                break
                            nl = lines[i + offset].strip()
                            if not nl or nl.lower().startswith("interpretation"):
                                break
                            # Skip method lines
                            if re.match(r'^(VISUAL|WET MOUNT|Tube|Calculated|Electrical|colorimetric|Ion Exchange|Double Indicator|CLIA|Flow cytometry)', nl, re.IGNORECASE):
                                continue
                            dm2 = _descriptive_values_re.match(nl)
                            if dm2:
                                value = dm2.group(1).strip()
                                break
                            # Also accept qualitative values
                            qm2 = _qual_re.match(nl)
                            if qm2:
                                value = qm2.group(1).strip()
                                break
                        if not value:
                            continue
                    norm = info["normal"]
                    if norm:
                        status = "normal" if value.upper().replace(" ", "") == norm.upper().replace(" ", "") else "abnormal"
                    else:
                        status = "noted"
                    results.append({
                        "test_name": test_name, "value": value,
                        "unit": "", "normal_range": norm or "—",
                        "status": status,
                    })
                    found_tests.add(test_name)
                    found = True
                    break
                if found:
                    break

        results.sort(key=lambda x: x["test_name"])
        return results

    def extract_from_image(self, image_bytes: bytes) -> Dict:
        """Full pipeline: OCR image/PDF → parse lab values"""
        raw_text = self.extract_text(image_bytes)
        lab_results = self.parse_lab_report(raw_text)
        return {
            "raw_text": raw_text,
            "lab_results": lab_results,
            "count": len(lab_results),
        }

    def _ocr_decimal_fix(self, test_name: str, value: float) -> float:
        """Fix OCR-missing decimal points by checking against normal range.
        
        Only triggers when value is >10x outside the normal range (clearly an
        OCR error, not a real abnormal result). E.g.:
        - sodium=14026 (normal 136-145) → 14026 > 145*10 → try 140.26 → fixed
        - ESR=61 (normal 0-20) → 61 < 20*10=200 → keep as-is (real abnormal)
        """
        normal_str = LAB_PATTERNS.get(test_name, {}).get("normal", "")
        if not normal_str:
            return value
        try:
            if normal_str.startswith("<"):
                high = float(normal_str[1:])
                low = 0
            elif normal_str.startswith(">"):
                low = float(normal_str[1:])
                high = low * 100
            elif "-" in normal_str:
                parts = normal_str.split("-")
                low, high = float(parts[0]), float(parts[1])
            else:
                return value
        except (ValueError, IndexError):
            return value

        # If within 10x of the range, keep it (could be a real abnormal value)
        if value <= high * 10 and (low == 0 or value >= low * 0.01):
            return value

        # Try inserting decimal at various positions
        s = str(int(value)) if value == int(value) else str(value)
        s_nodot = s.replace('.', '')
        for pos in range(1, len(s_nodot)):
            candidate = s_nodot[:pos] + '.' + s_nodot[pos:]
            try:
                cv = float(candidate)
                if low * 0.3 <= cv <= high * 3:
                    return cv
            except ValueError:
                continue
        return value

    def _assess_value(self, test_name: str, value: float) -> str:
        """Assess if a lab value is normal, high, or low"""
        normal_str = LAB_PATTERNS.get(test_name, {}).get("normal", "")
        if not normal_str:
            return "unknown"

        try:
            if normal_str.startswith("<"):
                threshold = float(normal_str[1:])
                return "normal" if value < threshold else "high"
            elif normal_str.startswith(">"):
                threshold = float(normal_str[1:])
                return "normal" if value > threshold else "low"
            elif "-" in normal_str:
                low_s, high_s = normal_str.split("-")
                low_v, high_v = float(low_s), float(high_s)
                if value < low_v:
                    return "low"
                elif value > high_v:
                    return "high"
                return "normal"
        except (ValueError, IndexError):
            pass
        return "unknown"

    def check_health(self) -> bool:
        return True
