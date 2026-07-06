"""
Medical Reference Data
Comprehensive lab test catalog with normal ranges, units, categories, and autocomplete support.
Also includes risk models, specialist prompts, screening guidelines, and lab interpretation engine.
"""

from typing import Dict, List, Optional

# ══════════════════════════════════════════════════════════════════
#  LAB TEST CATALOG — name, unit, normal_range, category
# ══════════════════════════════════════════════════════════════════

LAB_TEST_CATALOG = [
    # ── Complete Blood Count (CBC) ──
    {"name": "hemoglobin", "display": "Hemoglobin (Hb)", "unit": "g/dL", "normal_range": "12.0-17.5", "category": "CBC"},
    {"name": "rbc_count", "display": "RBC Count", "unit": "million/µL", "normal_range": "4.5-5.5", "category": "CBC"},
    {"name": "wbc_count", "display": "WBC Count (TLC)", "unit": "cells/µL", "normal_range": "4000-11000", "category": "CBC"},
    {"name": "platelet_count", "display": "Platelet Count", "unit": "lakh/µL", "normal_range": "1.5-4.0", "category": "CBC"},
    {"name": "hematocrit", "display": "Hematocrit (PCV)", "unit": "%", "normal_range": "36-54", "category": "CBC"},
    {"name": "mcv", "display": "MCV", "unit": "fL", "normal_range": "80-100", "category": "CBC"},
    {"name": "mch", "display": "MCH", "unit": "pg", "normal_range": "27-33", "category": "CBC"},
    {"name": "mchc", "display": "MCHC", "unit": "g/dL", "normal_range": "32-36", "category": "CBC"},
    {"name": "rdw", "display": "RDW", "unit": "%", "normal_range": "11.5-14.5", "category": "CBC"},
    {"name": "mpv", "display": "MPV", "unit": "fL", "normal_range": "7.5-11.5", "category": "CBC"},
    {"name": "neutrophils", "display": "Neutrophils", "unit": "%", "normal_range": "40-70", "category": "CBC"},
    {"name": "lymphocytes", "display": "Lymphocytes", "unit": "%", "normal_range": "20-40", "category": "CBC"},
    {"name": "monocytes", "display": "Monocytes", "unit": "%", "normal_range": "2-8", "category": "CBC"},
    {"name": "eosinophils", "display": "Eosinophils", "unit": "%", "normal_range": "1-4", "category": "CBC"},
    {"name": "basophils", "display": "Basophils", "unit": "%", "normal_range": "0-1", "category": "CBC"},
    {"name": "esr", "display": "ESR", "unit": "mm/hr", "normal_range": "0-20", "category": "CBC"},

    # ── Blood Sugar ──
    {"name": "fasting_glucose", "display": "Fasting Blood Glucose", "unit": "mg/dL", "normal_range": "70-100", "category": "Sugar"},
    {"name": "pp_glucose", "display": "Post Prandial Glucose", "unit": "mg/dL", "normal_range": "70-140", "category": "Sugar"},
    {"name": "random_glucose", "display": "Random Blood Glucose", "unit": "mg/dL", "normal_range": "70-140", "category": "Sugar"},
    {"name": "hba1c", "display": "HbA1c (Glycated Hemoglobin)", "unit": "%", "normal_range": "4.0-5.6", "category": "Sugar"},
    {"name": "fasting_insulin", "display": "Fasting Insulin", "unit": "µIU/mL", "normal_range": "2.6-24.9", "category": "Sugar"},

    # ── Lipid Profile ──
    {"name": "total_cholesterol", "display": "Total Cholesterol", "unit": "mg/dL", "normal_range": "<200", "category": "Lipid"},
    {"name": "ldl_cholesterol", "display": "LDL Cholesterol", "unit": "mg/dL", "normal_range": "<100", "category": "Lipid"},
    {"name": "hdl_cholesterol", "display": "HDL Cholesterol", "unit": "mg/dL", "normal_range": "40-60", "category": "Lipid"},
    {"name": "vldl_cholesterol", "display": "VLDL Cholesterol", "unit": "mg/dL", "normal_range": "5-40", "category": "Lipid"},
    {"name": "triglycerides", "display": "Triglycerides", "unit": "mg/dL", "normal_range": "<150", "category": "Lipid"},
    {"name": "cholesterol_hdl_ratio", "display": "Cholesterol/HDL Ratio", "unit": "", "normal_range": "<5.0", "category": "Lipid"},

    # ── Liver Function (LFT) ──
    {"name": "sgot_ast", "display": "SGOT (AST)", "unit": "U/L", "normal_range": "5-40", "category": "Liver"},
    {"name": "sgpt_alt", "display": "SGPT (ALT)", "unit": "U/L", "normal_range": "7-56", "category": "Liver"},
    {"name": "alkaline_phosphatase", "display": "Alkaline Phosphatase (ALP)", "unit": "U/L", "normal_range": "44-147", "category": "Liver"},
    {"name": "ggt", "display": "GGT (Gamma GT)", "unit": "U/L", "normal_range": "0-45", "category": "Liver"},
    {"name": "total_bilirubin", "display": "Total Bilirubin", "unit": "mg/dL", "normal_range": "0.1-1.2", "category": "Liver"},
    {"name": "direct_bilirubin", "display": "Direct Bilirubin", "unit": "mg/dL", "normal_range": "0.0-0.3", "category": "Liver"},
    {"name": "indirect_bilirubin", "display": "Indirect Bilirubin", "unit": "mg/dL", "normal_range": "0.1-0.9", "category": "Liver"},
    {"name": "total_protein", "display": "Total Protein", "unit": "g/dL", "normal_range": "6.0-8.3", "category": "Liver"},
    {"name": "albumin", "display": "Albumin", "unit": "g/dL", "normal_range": "3.5-5.5", "category": "Liver"},
    {"name": "globulin", "display": "Globulin", "unit": "g/dL", "normal_range": "2.0-3.5", "category": "Liver"},
    {"name": "ag_ratio", "display": "A/G Ratio", "unit": "", "normal_range": "1.0-2.5", "category": "Liver"},

    # ── Kidney Function (KFT/RFT) ──
    {"name": "urea", "display": "Blood Urea", "unit": "mg/dL", "normal_range": "7-20", "category": "Kidney"},
    {"name": "bun", "display": "BUN (Blood Urea Nitrogen)", "unit": "mg/dL", "normal_range": "7-20", "category": "Kidney"},
    {"name": "creatinine", "display": "Serum Creatinine", "unit": "mg/dL", "normal_range": "0.7-1.3", "category": "Kidney"},
    {"name": "uric_acid", "display": "Uric Acid", "unit": "mg/dL", "normal_range": "3.5-7.2", "category": "Kidney"},
    {"name": "egfr", "display": "eGFR", "unit": "mL/min/1.73m²", "normal_range": ">90", "category": "Kidney"},
    {"name": "bun_creatinine_ratio", "display": "BUN/Creatinine Ratio", "unit": "", "normal_range": "10-20", "category": "Kidney"},
    {"name": "sodium", "display": "Sodium (Na)", "unit": "mEq/L", "normal_range": "136-145", "category": "Kidney"},
    {"name": "potassium", "display": "Potassium (K)", "unit": "mEq/L", "normal_range": "3.5-5.0", "category": "Kidney"},
    {"name": "chloride", "display": "Chloride (Cl)", "unit": "mEq/L", "normal_range": "98-106", "category": "Kidney"},
    {"name": "calcium", "display": "Calcium (Ca)", "unit": "mg/dL", "normal_range": "8.5-10.5", "category": "Kidney"},
    {"name": "phosphorus", "display": "Phosphorus", "unit": "mg/dL", "normal_range": "2.5-4.5", "category": "Kidney"},
    {"name": "magnesium", "display": "Magnesium (Mg)", "unit": "mg/dL", "normal_range": "1.7-2.2", "category": "Kidney"},

    # ── Thyroid ──
    {"name": "tsh", "display": "TSH", "unit": "µIU/mL", "normal_range": "0.4-4.0", "category": "Thyroid"},
    {"name": "t3", "display": "T3 (Triiodothyronine)", "unit": "ng/dL", "normal_range": "80-200", "category": "Thyroid"},
    {"name": "t4", "display": "T4 (Thyroxine)", "unit": "µg/dL", "normal_range": "5.0-12.0", "category": "Thyroid"},
    {"name": "free_t3", "display": "Free T3", "unit": "pg/mL", "normal_range": "2.0-4.4", "category": "Thyroid"},
    {"name": "free_t4", "display": "Free T4", "unit": "ng/dL", "normal_range": "0.9-1.7", "category": "Thyroid"},

    # ── Iron Studies ──
    {"name": "serum_iron", "display": "Serum Iron", "unit": "µg/dL", "normal_range": "60-170", "category": "Iron"},
    {"name": "ferritin", "display": "Ferritin", "unit": "ng/mL", "normal_range": "12-300", "category": "Iron"},
    {"name": "tibc", "display": "TIBC", "unit": "µg/dL", "normal_range": "250-370", "category": "Iron"},
    {"name": "transferrin_saturation", "display": "Transferrin Saturation", "unit": "%", "normal_range": "20-50", "category": "Iron"},

    # ── Vitamins ──
    {"name": "vitamin_d", "display": "Vitamin D (25-OH)", "unit": "ng/mL", "normal_range": "30-100", "category": "Vitamins"},
    {"name": "vitamin_b12", "display": "Vitamin B12", "unit": "pg/mL", "normal_range": "200-900", "category": "Vitamins"},
    {"name": "folate", "display": "Folate (Folic Acid)", "unit": "ng/mL", "normal_range": "2.7-17.0", "category": "Vitamins"},

    # ── Cardiac Markers ──
    {"name": "troponin_i", "display": "Troponin I", "unit": "ng/mL", "normal_range": "<0.04", "category": "Cardiac"},
    {"name": "troponin_t", "display": "Troponin T", "unit": "ng/mL", "normal_range": "<0.01", "category": "Cardiac"},
    {"name": "ck_mb", "display": "CK-MB", "unit": "U/L", "normal_range": "0-25", "category": "Cardiac"},
    {"name": "bnp", "display": "BNP", "unit": "pg/mL", "normal_range": "<100", "category": "Cardiac"},
    {"name": "nt_pro_bnp", "display": "NT-proBNP", "unit": "pg/mL", "normal_range": "<125", "category": "Cardiac"},
    {"name": "crp", "display": "CRP (C-Reactive Protein)", "unit": "mg/L", "normal_range": "<3.0", "category": "Cardiac"},
    {"name": "hs_crp", "display": "hs-CRP", "unit": "mg/L", "normal_range": "<1.0", "category": "Cardiac"},
    {"name": "homocysteine", "display": "Homocysteine", "unit": "µmol/L", "normal_range": "5-15", "category": "Cardiac"},

    # ── Diabetes Extended ──
    {"name": "c_peptide", "display": "C-Peptide", "unit": "ng/mL", "normal_range": "0.8-3.1", "category": "Sugar"},
    {"name": "microalbumin_urine", "display": "Microalbumin (Urine)", "unit": "mg/L", "normal_range": "<30", "category": "Kidney"},

    # ── Urine Analysis ──
    {"name": "urine_ph", "display": "Urine pH", "unit": "", "normal_range": "4.5-8.0", "category": "Urine"},
    {"name": "urine_specific_gravity", "display": "Urine Specific Gravity", "unit": "", "normal_range": "1.005-1.030", "category": "Urine"},
    {"name": "urine_protein", "display": "Urine Protein", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_glucose", "display": "Urine Glucose", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_ketone", "display": "Urine Ketone", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_blood", "display": "Urine Blood", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_bilirubin", "display": "Urine Bilirubin", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_urobilinogen", "display": "Urine Urobilinogen", "unit": "mg/dL", "normal_range": "0.2-1.0", "category": "Urine"},
    {"name": "urine_nitrite", "display": "Urine Nitrite", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_leukocytes", "display": "Urine Leukocytes", "unit": "", "normal_range": "Negative", "category": "Urine"},
    {"name": "urine_rbc", "display": "Urine RBC", "unit": "/HPF", "normal_range": "0-2", "category": "Urine"},
    {"name": "urine_wbc", "display": "Urine WBC (Pus Cells)", "unit": "/HPF", "normal_range": "0-5", "category": "Urine"},
    {"name": "urine_epithelial", "display": "Urine Epithelial Cells", "unit": "/HPF", "normal_range": "0-5", "category": "Urine"},
    {"name": "urine_cast", "display": "Urine Cast", "unit": "/LPF", "normal_range": "0-2", "category": "Urine"},
    {"name": "urine_crystals", "display": "Urine Crystals", "unit": "", "normal_range": "Absent", "category": "Urine"},
    {"name": "urine_bacteria", "display": "Urine Bacteria", "unit": "", "normal_range": "Absent", "category": "Urine"},

    # ── Vitals (manually entered) ──
    {"name": "blood_pressure_systolic", "display": "Blood Pressure (Systolic)", "unit": "mmHg", "normal_range": "90-120", "category": "Vitals"},
    {"name": "blood_pressure_diastolic", "display": "Blood Pressure (Diastolic)", "unit": "mmHg", "normal_range": "60-80", "category": "Vitals"},
    {"name": "heart_rate", "display": "Heart Rate (Pulse)", "unit": "bpm", "normal_range": "60-100", "category": "Vitals"},
    {"name": "body_temperature", "display": "Body Temperature", "unit": "°F", "normal_range": "97.8-99.1", "category": "Vitals"},
    {"name": "respiratory_rate", "display": "Respiratory Rate", "unit": "/min", "normal_range": "12-20", "category": "Vitals"},
    {"name": "spo2", "display": "SpO2 (Oxygen Saturation)", "unit": "%", "normal_range": "95-100", "category": "Vitals"},
    {"name": "bmi", "display": "BMI (Body Mass Index)", "unit": "kg/m²", "normal_range": "18.5-24.9", "category": "Vitals"},
    {"name": "weight", "display": "Weight", "unit": "kg", "normal_range": "", "category": "Vitals"},
    {"name": "height", "display": "Height", "unit": "cm", "normal_range": "", "category": "Vitals"},

    # ── Hormones ──
    {"name": "testosterone", "display": "Testosterone", "unit": "ng/dL", "normal_range": "300-1000", "category": "Hormones"},
    {"name": "estradiol", "display": "Estradiol (E2)", "unit": "pg/mL", "normal_range": "15-350", "category": "Hormones"},
    {"name": "prolactin", "display": "Prolactin", "unit": "ng/mL", "normal_range": "2-18", "category": "Hormones"},
    {"name": "cortisol", "display": "Cortisol (Morning)", "unit": "µg/dL", "normal_range": "6-23", "category": "Hormones"},
    {"name": "dhea_s", "display": "DHEA-S", "unit": "µg/dL", "normal_range": "80-560", "category": "Hormones"},
    {"name": "lh", "display": "LH (Luteinizing Hormone)", "unit": "mIU/mL", "normal_range": "1.5-9.3", "category": "Hormones"},
    {"name": "fsh", "display": "FSH (Follicle Stimulating)", "unit": "mIU/mL", "normal_range": "1.4-18.1", "category": "Hormones"},

    # ── Coagulation ──
    {"name": "pt_inr", "display": "PT/INR", "unit": "", "normal_range": "0.8-1.2", "category": "Coagulation"},
    {"name": "aptt", "display": "aPTT", "unit": "seconds", "normal_range": "25-35", "category": "Coagulation"},
    {"name": "d_dimer", "display": "D-Dimer", "unit": "ng/mL", "normal_range": "<500", "category": "Coagulation"},
    {"name": "fibrinogen", "display": "Fibrinogen", "unit": "mg/dL", "normal_range": "200-400", "category": "Coagulation"},
    {"name": "bleeding_time", "display": "Bleeding Time", "unit": "minutes", "normal_range": "2-7", "category": "Coagulation"},
    {"name": "clotting_time", "display": "Clotting Time", "unit": "minutes", "normal_range": "4-9", "category": "Coagulation"},

    # ── Pancreas ──
    {"name": "amylase", "display": "Amylase", "unit": "U/L", "normal_range": "28-100", "category": "Pancreas"},
    {"name": "lipase", "display": "Lipase", "unit": "U/L", "normal_range": "0-160", "category": "Pancreas"},

    # ── Tumor Markers ──
    {"name": "psa", "display": "PSA (Prostate Specific Antigen)", "unit": "ng/mL", "normal_range": "<4.0", "category": "Tumor Markers"},
    {"name": "cea", "display": "CEA", "unit": "ng/mL", "normal_range": "<3.0", "category": "Tumor Markers"},
    {"name": "afp", "display": "AFP (Alpha-Fetoprotein)", "unit": "ng/mL", "normal_range": "<10", "category": "Tumor Markers"},
    {"name": "ca_125", "display": "CA-125", "unit": "U/mL", "normal_range": "<35", "category": "Tumor Markers"},
    {"name": "ca_19_9", "display": "CA 19-9", "unit": "U/mL", "normal_range": "<37", "category": "Tumor Markers"},

    # ── Infection Markers ──
    {"name": "procalcitonin", "display": "Procalcitonin", "unit": "ng/mL", "normal_range": "<0.1", "category": "Infection"},
    {"name": "il_6", "display": "IL-6 (Interleukin 6)", "unit": "pg/mL", "normal_range": "<7", "category": "Infection"},
    {"name": "ldh", "display": "LDH (Lactate Dehydrogenase)", "unit": "U/L", "normal_range": "140-280", "category": "Infection"},

    # ── HPLC / Hemoglobin Variants ──
    {"name": "hb_a", "display": "Hb A", "unit": "%", "normal_range": "95-98", "category": "HPLC"},
    {"name": "hb_a2", "display": "Hb A2", "unit": "%", "normal_range": "2.0-3.3", "category": "HPLC"},
    {"name": "hb_f", "display": "Hb F (Fetal)", "unit": "%", "normal_range": "<1.0", "category": "HPLC"},
    {"name": "hb_s", "display": "Hb S (Sickle)", "unit": "%", "normal_range": "0", "category": "HPLC"},
]

# Quick-lookup dict: name → catalog entry
LAB_CATALOG_MAP = {t["name"]: t for t in LAB_TEST_CATALOG}

# Category list
LAB_CATEGORIES = sorted(set(t["category"] for t in LAB_TEST_CATALOG))


# ══════════════════════════════════════════════════════════════════
#  SPECIALIST PERSONAS
# ══════════════════════════════════════════════════════════════════

SPECIALIST_PROMPTS = {
    "general": {
        "name": "General Physician",
        "icon": "🩺",
        "prompt": "You are a General Physician (GP). Approach the patient holistically. Consider common conditions first. Refer to specialists when needed."
    },
    "cardiologist": {
        "name": "Cardiologist",
        "icon": "❤️",
        "prompt": "You are a Cardiologist. Focus on cardiovascular health. Consider heart disease, hypertension, arrhythmias, cholesterol, and cardiac risk factors. Interpret ECG findings, cardiac markers (troponin, BNP), and lipid profiles with expert-level precision."
    },
    "dermatologist": {
        "name": "Dermatologist",
        "icon": "🧴",
        "prompt": "You are a Dermatologist. Analyze skin conditions from descriptions and images. Consider rashes, eczema, psoriasis, fungal infections, acne, and suspicious lesions. Recommend appropriate topical treatments and when to biopsy."
    },
    "endocrinologist": {
        "name": "Endocrinologist",
        "icon": "🧬",
        "prompt": "You are an Endocrinologist. Focus on hormonal and metabolic disorders including diabetes, thyroid conditions, PCOS, adrenal disorders, and metabolic syndrome. Interpret HbA1c, thyroid panels, and hormone levels with precision."
    },
    "neurologist": {
        "name": "Neurologist",
        "icon": "🧠",
        "prompt": "You are a Neurologist. Focus on neurological conditions — headaches, migraines, seizures, neuropathy, stroke risk, cognitive issues. Evaluate neurological symptoms systematically."
    },
    "gastroenterologist": {
        "name": "Gastroenterologist",
        "icon": "🫁",
        "prompt": "You are a Gastroenterologist. Focus on digestive system — GERD, IBS, liver disease, pancreatitis, celiac disease. Interpret LFT, stool tests, and abdominal symptoms."
    },
    "nephrologist": {
        "name": "Nephrologist",
        "icon": "🫘",
        "prompt": "You are a Nephrologist. Focus on kidney health. Interpret creatinine, BUN, eGFR, urine analysis. Assess CKD staging, electrolyte imbalances, and renal complications."
    },
    "psychiatrist": {
        "name": "Psychiatrist",
        "icon": "💭",
        "prompt": "You are a Psychiatrist. Approach mental health with empathy. Assess depression, anxiety, sleep disorders, PTSD, bipolar disorder. Use validated screening tools (PHQ-9, GAD-7). Always prioritize safety."
    },
    "nutritionist": {
        "name": "Nutritionist",
        "icon": "🥗",
        "prompt": "You are a Clinical Nutritionist. Design evidence-based dietary plans. Address nutritional deficiencies, weight management, diabetes diet, heart-healthy eating, and food sensitivities."
    },
    "orthopedist": {
        "name": "Orthopedist",
        "icon": "🦴",
        "prompt": "You are an Orthopedic Specialist. Focus on bones, joints, muscles, ligaments. Evaluate fractures, arthritis, back pain, sports injuries. Interpret X-rays for skeletal abnormalities."
    },
    "pulmonologist": {
        "name": "Pulmonologist",
        "icon": "🫁",
        "prompt": "You are a Pulmonologist. Focus on respiratory conditions — asthma, COPD, pneumonia, TB, lung infections. Interpret chest X-rays, SpO2, and respiratory function."
    },
    "radiologist": {
        "name": "Radiologist",
        "icon": "📡",
        "prompt": "You are a Radiologist. Provide detailed interpretation of medical imaging — X-rays, CTs, MRIs. Describe findings systematically: technique, findings, impression, recommendation."
    },
}


# ══════════════════════════════════════════════════════════════════
#  RISK FACTORS AND DISEASE RULES
# ══════════════════════════════════════════════════════════════════

RISK_RULES = {
    "type_2_diabetes": {
        "name": "Type-2 Diabetes",
        "factors": [
            {"test": "fasting_glucose", "threshold": 100, "op": ">", "weight": 20},
            {"test": "hba1c", "threshold": 5.7, "op": ">", "weight": 25},
            {"test": "fasting_insulin", "threshold": 15, "op": ">", "weight": 10},
            {"test": "bmi", "threshold": 25, "op": ">", "weight": 15},
            {"test": "triglycerides", "threshold": 150, "op": ">", "weight": 10},
            {"test": "hdl_cholesterol", "threshold": 40, "op": "<", "weight": 10},
        ],
        "age_factor": {"over": 45, "weight": 10},
    },
    "heart_disease": {
        "name": "Heart Disease",
        "factors": [
            {"test": "ldl_cholesterol", "threshold": 130, "op": ">", "weight": 20},
            {"test": "total_cholesterol", "threshold": 200, "op": ">", "weight": 10},
            {"test": "hdl_cholesterol", "threshold": 40, "op": "<", "weight": 15},
            {"test": "triglycerides", "threshold": 200, "op": ">", "weight": 10},
            {"test": "hs_crp", "threshold": 3.0, "op": ">", "weight": 15},
            {"test": "homocysteine", "threshold": 15, "op": ">", "weight": 10},
            {"test": "blood_pressure_systolic", "threshold": 140, "op": ">", "weight": 15},
        ],
        "age_factor": {"over": 50, "weight": 5},
    },
    "stroke": {
        "name": "Stroke",
        "factors": [
            {"test": "blood_pressure_systolic", "threshold": 140, "op": ">", "weight": 25},
            {"test": "ldl_cholesterol", "threshold": 160, "op": ">", "weight": 15},
            {"test": "hba1c", "threshold": 6.5, "op": ">", "weight": 15},
            {"test": "d_dimer", "threshold": 500, "op": ">", "weight": 15},
        ],
        "age_factor": {"over": 55, "weight": 10},
    },
    "hypertension": {
        "name": "Hypertension",
        "factors": [
            {"test": "blood_pressure_systolic", "threshold": 130, "op": ">", "weight": 30},
            {"test": "blood_pressure_diastolic", "threshold": 80, "op": ">", "weight": 25},
            {"test": "sodium", "threshold": 145, "op": ">", "weight": 10},
            {"test": "bmi", "threshold": 30, "op": ">", "weight": 15},
            {"test": "creatinine", "threshold": 1.3, "op": ">", "weight": 10},
        ],
        "age_factor": {"over": 40, "weight": 10},
    },
    "kidney_disease": {
        "name": "Kidney Disease",
        "factors": [
            {"test": "creatinine", "threshold": 1.3, "op": ">", "weight": 25},
            {"test": "bun", "threshold": 20, "op": ">", "weight": 15},
            {"test": "egfr", "threshold": 60, "op": "<", "weight": 25},
            {"test": "uric_acid", "threshold": 7.0, "op": ">", "weight": 10},
            {"test": "microalbumin_urine", "threshold": 30, "op": ">", "weight": 15},
            {"test": "potassium", "threshold": 5.0, "op": ">", "weight": 10},
        ],
        "age_factor": {"over": 60, "weight": 5},
    },
    "liver_disease": {
        "name": "Liver Disease",
        "factors": [
            {"test": "sgpt_alt", "threshold": 56, "op": ">", "weight": 20},
            {"test": "sgot_ast", "threshold": 40, "op": ">", "weight": 15},
            {"test": "total_bilirubin", "threshold": 1.2, "op": ">", "weight": 15},
            {"test": "ggt", "threshold": 45, "op": ">", "weight": 15},
            {"test": "alkaline_phosphatase", "threshold": 147, "op": ">", "weight": 10},
            {"test": "albumin", "threshold": 3.5, "op": "<", "weight": 15},
        ],
    },
    "thyroid_disorder": {
        "name": "Thyroid Disorder",
        "factors": [
            {"test": "tsh", "threshold": 4.0, "op": ">", "weight": 30},
            {"test": "free_t4", "threshold": 0.9, "op": "<", "weight": 20},
            {"test": "free_t3", "threshold": 2.0, "op": "<", "weight": 15},
        ],
    },
    "anemia": {
        "name": "Anemia",
        "factors": [
            {"test": "hemoglobin", "threshold": 12.0, "op": "<", "weight": 30},
            {"test": "ferritin", "threshold": 12, "op": "<", "weight": 20},
            {"test": "serum_iron", "threshold": 60, "op": "<", "weight": 15},
            {"test": "mcv", "threshold": 80, "op": "<", "weight": 10},
        ],
    },
}


# ══════════════════════════════════════════════════════════════════
#  PREVENTIVE SCREENING GUIDELINES (age-based)
# ══════════════════════════════════════════════════════════════════

SCREENING_GUIDELINES = [
    {"min_age": 18, "max_age": 120, "test": "Complete Blood Count (CBC)", "frequency": "Annually", "priority": "high"},
    {"min_age": 18, "max_age": 120, "test": "Fasting Blood Glucose", "frequency": "Annually", "priority": "high"},
    {"min_age": 20, "max_age": 120, "test": "Lipid Profile", "frequency": "Every 5 years (annually if risk)", "priority": "high"},
    {"min_age": 18, "max_age": 120, "test": "Liver Function Test (LFT)", "frequency": "Annually", "priority": "medium"},
    {"min_age": 18, "max_age": 120, "test": "Kidney Function Test (KFT)", "frequency": "Annually", "priority": "medium"},
    {"min_age": 30, "max_age": 120, "test": "Thyroid Panel (TSH, T3, T4)", "frequency": "Every 2 years", "priority": "medium"},
    {"min_age": 18, "max_age": 120, "test": "Vitamin D", "frequency": "Annually", "priority": "medium"},
    {"min_age": 18, "max_age": 120, "test": "Vitamin B12", "frequency": "Annually", "priority": "medium"},
    {"min_age": 18, "max_age": 120, "test": "Iron Studies (Ferritin, TIBC)", "frequency": "Annually if anemic", "priority": "medium"},
    {"min_age": 25, "max_age": 120, "test": "HbA1c", "frequency": "Annually (every 3 months if diabetic)", "priority": "high"},
    {"min_age": 40, "max_age": 120, "test": "ECG / Cardiac Risk", "frequency": "Annually", "priority": "high"},
    {"min_age": 40, "max_age": 120, "test": "Blood Pressure Monitoring", "frequency": "Every visit", "priority": "high"},
    {"min_age": 50, "max_age": 120, "test": "PSA (Males)", "frequency": "Annually", "priority": "medium", "gender": "male"},
    {"min_age": 40, "max_age": 120, "test": "Mammography (Females)", "frequency": "Every 2 years", "priority": "high", "gender": "female"},
    {"min_age": 50, "max_age": 120, "test": "Colonoscopy", "frequency": "Every 10 years", "priority": "medium"},
    {"min_age": 30, "max_age": 120, "test": "Urine Analysis", "frequency": "Annually", "priority": "low"},
    {"min_age": 45, "max_age": 120, "test": "Chest X-Ray", "frequency": "Every 2-3 years", "priority": "low"},
    {"min_age": 35, "max_age": 120, "test": "Eye Exam", "frequency": "Every 2 years", "priority": "low"},
    {"min_age": 50, "max_age": 120, "test": "Bone Density (DEXA) for Women", "frequency": "Every 2 years", "priority": "medium", "gender": "female"},
    {"min_age": 60, "max_age": 120, "test": "Vitamin B12 & Folate", "frequency": "Annually", "priority": "medium"},
]


# ══════════════════════════════════════════════════════════════════
#  LAB CORRELATION PATTERNS (cross-test intelligence)
# ══════════════════════════════════════════════════════════════════

LAB_CORRELATION_RULES = [
    {
        "id": "metabolic_syndrome",
        "name": "Metabolic Syndrome",
        "severity": "high",
        "tests": {"fasting_glucose": (">", 100), "triglycerides": (">", 150), "hdl_cholesterol": ("<", 40), "blood_pressure_systolic": (">", 130)},
        "min_matches": 3,
        "message": "Metabolic Syndrome indicators detected. Multiple metabolic risk factors present — high glucose, abnormal lipids, and elevated blood pressure together significantly increase cardiovascular and diabetes risk.",
        "recommendation": "Lifestyle modification is critical: reduce refined carbs, increase physical activity (150 min/week), target weight loss of 5-10%. Consult endocrinologist.",
    },
    {
        "id": "iron_deficiency_anemia",
        "name": "Iron Deficiency Anemia",
        "severity": "medium",
        "tests": {"hemoglobin": ("<", 12), "ferritin": ("<", 12), "serum_iron": ("<", 60), "mcv": ("<", 80)},
        "min_matches": 2,
        "message": "Iron Deficiency Anemia pattern detected. Low hemoglobin combined with depleted iron stores suggests chronic iron deficiency.",
        "recommendation": "Iron supplementation recommended. Investigate underlying cause (dietary deficiency, blood loss, malabsorption). Follow up with CBC in 4-6 weeks.",
    },
    {
        "id": "prediabetes",
        "name": "Pre-Diabetes",
        "severity": "medium",
        "tests": {"fasting_glucose": (">", 100), "hba1c": (">", 5.7), "fasting_insulin": (">", 15)},
        "min_matches": 2,
        "message": "Pre-diabetic pattern detected. Elevated fasting glucose and/or HbA1c indicate impaired glucose regulation.",
        "recommendation": "Dietary modification (reduce simple sugars), regular exercise, weight management. Retest in 3 months. Consider glucose tolerance test (OGTT).",
    },
    {
        "id": "liver_stress",
        "name": "Liver Stress / Hepatic Dysfunction",
        "severity": "medium",
        "tests": {"sgpt_alt": (">", 56), "sgot_ast": (">", 40), "total_bilirubin": (">", 1.2), "ggt": (">", 45)},
        "min_matches": 2,
        "message": "Liver stress pattern detected. Elevated liver enzymes suggest hepatocellular injury or biliary obstruction.",
        "recommendation": "Avoid alcohol, hepatotoxic drugs (paracetamol). Ultrasound abdomen recommended. Consult gastroenterologist if persistent.",
    },
    {
        "id": "kidney_impairment",
        "name": "Early Kidney Impairment",
        "severity": "high",
        "tests": {"creatinine": (">", 1.3), "bun": (">", 20), "egfr": ("<", 60), "potassium": (">", 5.0)},
        "min_matches": 2,
        "message": "Kidney impairment indicators detected. Elevated creatinine and/or reduced eGFR suggest declining kidney function.",
        "recommendation": "Control blood pressure and blood sugar. Limit protein and salt intake. Avoid NSAIDs. Nephrology referral recommended.",
    },
    {
        "id": "thyroid_hypo",
        "name": "Hypothyroidism",
        "severity": "medium",
        "tests": {"tsh": (">", 4.0), "free_t4": ("<", 0.9), "free_t3": ("<", 2.0)},
        "min_matches": 2,
        "message": "Hypothyroidism pattern detected. Elevated TSH with low thyroid hormones indicates underactive thyroid.",
        "recommendation": "Thyroid hormone replacement (levothyroxine) may be needed. Retest in 6-8 weeks. Monitor for symptoms (fatigue, weight gain, cold intolerance).",
    },
    {
        "id": "cardiovascular_risk",
        "name": "High Cardiovascular Risk",
        "severity": "high",
        "tests": {"ldl_cholesterol": (">", 130), "hdl_cholesterol": ("<", 40), "hs_crp": (">", 3.0), "triglycerides": (">", 200)},
        "min_matches": 2,
        "message": "Elevated cardiovascular risk. Abnormal lipid profile with inflammatory markers suggest increased risk of heart attack and stroke.",
        "recommendation": "Statin therapy may be indicated. Mediterranean diet, regular aerobic exercise (30 min/day), quit smoking. Cardiology consultation recommended.",
    },
    {
        "id": "vitamin_deficiency",
        "name": "Vitamin Deficiency Complex",
        "severity": "low",
        "tests": {"vitamin_d": ("<", 20), "vitamin_b12": ("<", 200), "folate": ("<", 2.7), "ferritin": ("<", 30)},
        "min_matches": 2,
        "message": "Multiple vitamin/mineral deficiencies detected. This can cause fatigue, weakness, cognitive issues, and impaired immunity.",
        "recommendation": "Supplementation recommended. Consider dietary assessment. Rule out malabsorption conditions (celiac, IBD).",
    },
    {
        "id": "infection_active",
        "name": "Active Infection / Inflammation",
        "severity": "medium",
        "tests": {"wbc_count": (">", 11000), "crp": (">", 10), "esr": (">", 30), "procalcitonin": (">", 0.5)},
        "min_matches": 2,
        "message": "Active infection or significant inflammation detected. Elevated WBC with inflammatory markers indicate an ongoing immune response.",
        "recommendation": "Identify source of infection. Blood cultures if febrile. May need antibiotic therapy. Urgent medical attention if sepsis suspected.",
    },
    {
        "id": "coagulation_risk",
        "name": "Coagulation Disorder Risk",
        "severity": "high",
        "tests": {"d_dimer": (">", 500), "pt_inr": (">", 1.5), "fibrinogen": (">", 400), "platelet_count": ("<", 1.0)},
        "min_matches": 2,
        "message": "Coagulation abnormality detected. Abnormal clotting parameters may indicate thrombotic or hemorrhagic risk.",
        "recommendation": "Urgent hematology evaluation. Avoid blood thinners without medical guidance. Monitor for signs of bleeding or clot formation.",
    },
]


# ══════════════════════════════════════════════════════════════════
#  ORGAN HEALTH SCORING RULES
# ══════════════════════════════════════════════════════════════════

ORGAN_HEALTH_RULES = {
    "heart": {
        "name": "Heart",
        "icon": "❤️",
        "tests": ["ldl_cholesterol", "hdl_cholesterol", "triglycerides", "total_cholesterol",
                  "hs_crp", "troponin_i", "bnp", "blood_pressure_systolic", "heart_rate", "homocysteine"],
    },
    "liver": {
        "name": "Liver",
        "icon": "🟤",
        "tests": ["sgpt_alt", "sgot_ast", "total_bilirubin", "direct_bilirubin", "alkaline_phosphatase",
                  "ggt", "total_protein", "albumin", "globulin", "ag_ratio"],
    },
    "kidney": {
        "name": "Kidneys",
        "icon": "🫘",
        "tests": ["creatinine", "bun", "uric_acid", "egfr", "sodium", "potassium",
                  "calcium", "phosphorus", "microalbumin_urine"],
    },
    "thyroid": {
        "name": "Thyroid",
        "icon": "🦋",
        "tests": ["tsh", "t3", "t4", "free_t3", "free_t4"],
    },
    "blood": {
        "name": "Blood",
        "icon": "🩸",
        "tests": ["hemoglobin", "rbc_count", "wbc_count", "platelet_count", "hematocrit",
                  "mcv", "mch", "mchc", "rdw", "esr"],
    },
    "pancreas": {
        "name": "Pancreas",
        "icon": "🟡",
        "tests": ["fasting_glucose", "hba1c", "fasting_insulin", "c_peptide", "amylase", "lipase"],
    },
    "bones": {
        "name": "Bones & Joints",
        "icon": "🦴",
        "tests": ["calcium", "phosphorus", "vitamin_d", "uric_acid", "alkaline_phosphatase"],
    },
    "lungs": {
        "name": "Lungs",
        "icon": "🫁",
        "tests": ["spo2", "respiratory_rate"],
    },
    "immune": {
        "name": "Immune System",
        "icon": "🛡️",
        "tests": ["wbc_count", "neutrophils", "lymphocytes", "crp", "esr", "vitamin_d"],
    },
}


def compute_risk_scores(lab_values: dict, age: int = None) -> list:
    """Compute disease risk scores from lab values.
    lab_values: dict of {test_name: float_value}
    Returns list of {disease, risk_pct, factors, top_contributors}
    """
    results = []
    for disease_id, rule in RISK_RULES.items():
        total_weight = sum(f["weight"] for f in rule["factors"])
        if "age_factor" in rule:
            total_weight += rule["age_factor"]["weight"]
        
        score = 0
        contributors = []
        for f in rule["factors"]:
            val = lab_values.get(f["test"])
            if val is None:
                continue
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
            triggered = (f["op"] == ">" and val > f["threshold"]) or (f["op"] == "<" and val < f["threshold"])
            if triggered:
                score += f["weight"]
                cat = LAB_CATALOG_MAP.get(f["test"], {})
                contributors.append(f"{cat.get('display', f['test'])}: {val} {cat.get('unit','')}")
        
        if age and "age_factor" in rule and age > rule["age_factor"]["over"]:
            score += rule["age_factor"]["weight"]
            contributors.append(f"Age: {age} (over {rule['age_factor']['over']})")
        
        risk_pct = min(95, round((score / total_weight) * 100)) if total_weight > 0 else 0
        if risk_pct > 0:
            results.append({
                "disease": rule["name"],
                "risk_pct": risk_pct,
                "level": "high" if risk_pct >= 60 else "moderate" if risk_pct >= 30 else "low",
                "contributors": contributors,
            })
    
    results.sort(key=lambda x: x["risk_pct"], reverse=True)
    return results


def compute_organ_scores(lab_values: dict) -> list:
    """Compute organ-level health scores (0-100) based on available lab data."""
    results = []
    for organ_id, rule in ORGAN_HEALTH_RULES.items():
        matched = 0
        abnormal = 0
        for test_name in rule["tests"]:
            val = lab_values.get(test_name)
            if val is None:
                continue
            matched += 1
            cat = LAB_CATALOG_MAP.get(test_name, {})
            nr = cat.get("normal_range", "")
            if _is_abnormal(val, nr):
                abnormal += 1
        
        if matched == 0:
            score = None  # not enough data
        else:
            score = max(0, min(100, round(100 - (abnormal / matched) * 60)))
        
        results.append({
            "organ": rule["name"],
            "icon": rule["icon"],
            "score": score,
            "tests_available": matched,
            "tests_abnormal": abnormal,
            "grade": _score_grade(score) if score is not None else "N/A",
        })
    return results


def compute_lab_correlations(lab_values: dict) -> list:
    """Find cross-test correlation patterns."""
    findings = []
    for rule in LAB_CORRELATION_RULES:
        matches = 0
        triggered_tests = []
        for test_name, (op, threshold) in rule["tests"].items():
            val = lab_values.get(test_name)
            if val is None:
                continue
            try:
                val_f = float(val)
            except (ValueError, TypeError):
                continue
            hit = (op == ">" and val_f > threshold) or (op == "<" and val_f < threshold)
            if hit:
                matches += 1
                cat = LAB_CATALOG_MAP.get(test_name, {})
                triggered_tests.append(f"{cat.get('display', test_name)}: {val} {cat.get('unit','')}")
        
        if matches >= rule["min_matches"]:
            findings.append({
                "id": rule["id"],
                "name": rule["name"],
                "severity": rule["severity"],
                "message": rule["message"],
                "recommendation": rule["recommendation"],
                "triggered_tests": triggered_tests,
                "matches": matches,
            })
    
    findings.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3))
    return findings


def detect_trends(lab_history: list) -> list:
    """Detect trends from historical lab data.
    lab_history: list of {test_name, value, date} sorted by date
    Returns list of trend insights.
    """
    from collections import defaultdict
    by_test = defaultdict(list)
    for r in lab_history:
        try:
            by_test[r["test_name"]].append({"value": float(r["value"]), "date": r["date"]})
        except (ValueError, TypeError):
            continue
    
    trends = []
    for test_name, points in by_test.items():
        if len(points) < 2:
            continue
        points.sort(key=lambda x: x["date"])
        values = [p["value"] for p in points]
        dates = [p["date"] for p in points]
        
        # Simple trend: compare first half average vs second half average
        mid = len(values) // 2
        avg_first = sum(values[:mid]) / mid
        avg_second = sum(values[mid:]) / (len(values) - mid)
        change_pct = ((avg_second - avg_first) / avg_first * 100) if avg_first != 0 else 0
        
        if abs(change_pct) < 5:
            direction = "stable"
        elif change_pct > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        cat = LAB_CATALOG_MAP.get(test_name, {})
        nr = cat.get("normal_range", "")
        latest_abnormal = _is_abnormal(str(values[-1]), nr)
        
        if abs(change_pct) >= 10 or latest_abnormal:
            trends.append({
                "test_name": test_name,
                "display": cat.get("display", test_name),
                "direction": direction,
                "change_pct": round(change_pct, 1),
                "latest_value": values[-1],
                "earliest_value": values[0],
                "data_points": [{"value": p["value"], "date": p["date"]} for p in points],
                "normal_range": nr,
                "is_concerning": (direction == "increasing" and latest_abnormal) or (abs(change_pct) > 20),
            })
    
    trends.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return trends


def get_screening_plan(age: int, gender: str = None) -> list:
    """Get recommended screenings based on age and gender."""
    plan = []
    if age is None:
        return plan
    for s in SCREENING_GUIDELINES:
        if age < s["min_age"] or age > s["max_age"]:
            continue
        if s.get("gender") and gender and s["gender"] != gender.lower():
            continue
        plan.append({
            "test": s["test"],
            "frequency": s["frequency"],
            "priority": s["priority"],
        })
    return plan


# ══════════════════════════════════════════════════════════════════
#  MEDICINE CATALOG — name, common dosages (mg), category, use
# ══════════════════════════════════════════════════════════════════

MEDICINE_CATALOG = [
    # ── Pain / Fever / Anti-inflammatory ──
    {"name": "Paracetamol", "dosages": ["250mg", "325mg", "500mg", "650mg", "1000mg"], "category": "Analgesic", "use": "Pain, fever"},
    {"name": "Ibuprofen", "dosages": ["200mg", "400mg", "600mg", "800mg"], "category": "NSAID", "use": "Pain, inflammation, fever"},
    {"name": "Aspirin", "dosages": ["75mg", "81mg", "150mg", "300mg", "500mg"], "category": "NSAID", "use": "Pain, fever, blood thinner"},
    {"name": "Diclofenac", "dosages": ["25mg", "50mg", "75mg", "100mg"], "category": "NSAID", "use": "Pain, inflammation"},
    {"name": "Naproxen", "dosages": ["250mg", "375mg", "500mg"], "category": "NSAID", "use": "Pain, inflammation"},
    {"name": "Mefenamic Acid", "dosages": ["250mg", "500mg"], "category": "NSAID", "use": "Pain, menstrual cramps"},
    {"name": "Aceclofenac", "dosages": ["100mg", "200mg"], "category": "NSAID", "use": "Pain, arthritis"},
    {"name": "Tramadol", "dosages": ["50mg", "100mg", "200mg"], "category": "Opioid Analgesic", "use": "Moderate to severe pain"},
    {"name": "Nimesulide", "dosages": ["100mg"], "category": "NSAID", "use": "Pain, inflammation"},
    {"name": "Celecoxib", "dosages": ["100mg", "200mg"], "category": "COX-2 Inhibitor", "use": "Arthritis, pain"},

    # ── Antibiotics ──
    {"name": "Amoxicillin", "dosages": ["250mg", "500mg", "875mg"], "category": "Antibiotic", "use": "Bacterial infections"},
    {"name": "Azithromycin", "dosages": ["250mg", "500mg"], "category": "Antibiotic", "use": "Bacterial infections, respiratory"},
    {"name": "Ciprofloxacin", "dosages": ["250mg", "500mg", "750mg"], "category": "Antibiotic", "use": "Urinary, respiratory infections"},
    {"name": "Amoxicillin-Clavulanate", "dosages": ["375mg", "625mg", "1000mg"], "category": "Antibiotic", "use": "Bacterial infections"},
    {"name": "Cephalexin", "dosages": ["250mg", "500mg"], "category": "Antibiotic", "use": "Skin, urinary infections"},
    {"name": "Cefixime", "dosages": ["100mg", "200mg", "400mg"], "category": "Antibiotic", "use": "Respiratory, urinary infections"},
    {"name": "Doxycycline", "dosages": ["50mg", "100mg"], "category": "Antibiotic", "use": "Bacterial infections, acne"},
    {"name": "Metronidazole", "dosages": ["200mg", "400mg", "500mg"], "category": "Antibiotic", "use": "Anaerobic infections, dental"},
    {"name": "Levofloxacin", "dosages": ["250mg", "500mg", "750mg"], "category": "Antibiotic", "use": "Respiratory, urinary infections"},
    {"name": "Clindamycin", "dosages": ["150mg", "300mg"], "category": "Antibiotic", "use": "Skin, bone infections"},
    {"name": "Nitrofurantoin", "dosages": ["50mg", "100mg"], "category": "Antibiotic", "use": "Urinary tract infections"},
    {"name": "Ofloxacin", "dosages": ["200mg", "400mg"], "category": "Antibiotic", "use": "Bacterial infections"},
    {"name": "Cefpodoxime", "dosages": ["100mg", "200mg"], "category": "Antibiotic", "use": "Respiratory, urinary infections"},

    # ── Antacids / GI ──
    {"name": "Omeprazole", "dosages": ["10mg", "20mg", "40mg"], "category": "PPI", "use": "Acid reflux, GERD, ulcers"},
    {"name": "Pantoprazole", "dosages": ["20mg", "40mg"], "category": "PPI", "use": "Acid reflux, GERD"},
    {"name": "Ranitidine", "dosages": ["150mg", "300mg"], "category": "H2 Blocker", "use": "Acid reflux, ulcers"},
    {"name": "Esomeprazole", "dosages": ["20mg", "40mg"], "category": "PPI", "use": "GERD, acid reflux"},
    {"name": "Rabeprazole", "dosages": ["10mg", "20mg"], "category": "PPI", "use": "GERD, ulcers"},
    {"name": "Domperidone", "dosages": ["10mg", "20mg"], "category": "Antiemetic", "use": "Nausea, vomiting, bloating"},
    {"name": "Ondansetron", "dosages": ["4mg", "8mg"], "category": "Antiemetic", "use": "Nausea, vomiting"},
    {"name": "Sucralfate", "dosages": ["500mg", "1000mg"], "category": "GI Protectant", "use": "Ulcers, gastric protection"},
    {"name": "Loperamide", "dosages": ["2mg"], "category": "Antidiarrheal", "use": "Diarrhea"},
    {"name": "Bismuth Subsalicylate", "dosages": ["262mg", "524mg"], "category": "Antidiarrheal", "use": "Diarrhea, indigestion"},

    # ── Diabetes ──
    {"name": "Metformin", "dosages": ["250mg", "500mg", "750mg", "850mg", "1000mg"], "category": "Antidiabetic", "use": "Type 2 diabetes"},
    {"name": "Glimepiride", "dosages": ["1mg", "2mg", "3mg", "4mg"], "category": "Sulfonylurea", "use": "Type 2 diabetes"},
    {"name": "Glipizide", "dosages": ["2.5mg", "5mg", "10mg"], "category": "Sulfonylurea", "use": "Type 2 diabetes"},
    {"name": "Gliclazide", "dosages": ["30mg", "40mg", "60mg", "80mg"], "category": "Sulfonylurea", "use": "Type 2 diabetes"},
    {"name": "Sitagliptin", "dosages": ["25mg", "50mg", "100mg"], "category": "DPP-4 Inhibitor", "use": "Type 2 diabetes"},
    {"name": "Vildagliptin", "dosages": ["50mg"], "category": "DPP-4 Inhibitor", "use": "Type 2 diabetes"},
    {"name": "Pioglitazone", "dosages": ["15mg", "30mg", "45mg"], "category": "Thiazolidinedione", "use": "Type 2 diabetes"},
    {"name": "Empagliflozin", "dosages": ["10mg", "25mg"], "category": "SGLT2 Inhibitor", "use": "Type 2 diabetes"},
    {"name": "Dapagliflozin", "dosages": ["5mg", "10mg"], "category": "SGLT2 Inhibitor", "use": "Type 2 diabetes"},
    {"name": "Insulin Glargine", "dosages": ["100 IU/mL"], "category": "Insulin", "use": "Diabetes (long-acting)"},
    {"name": "Insulin Lispro", "dosages": ["100 IU/mL"], "category": "Insulin", "use": "Diabetes (rapid-acting)"},

    # ── Cardiovascular / Blood Pressure ──
    {"name": "Amlodipine", "dosages": ["2.5mg", "5mg", "10mg"], "category": "CCB", "use": "Hypertension, angina"},
    {"name": "Atenolol", "dosages": ["25mg", "50mg", "100mg"], "category": "Beta Blocker", "use": "Hypertension, heart rate"},
    {"name": "Metoprolol", "dosages": ["25mg", "50mg", "100mg", "200mg"], "category": "Beta Blocker", "use": "Hypertension, heart failure"},
    {"name": "Losartan", "dosages": ["25mg", "50mg", "100mg"], "category": "ARB", "use": "Hypertension, kidney protection"},
    {"name": "Telmisartan", "dosages": ["20mg", "40mg", "80mg"], "category": "ARB", "use": "Hypertension"},
    {"name": "Enalapril", "dosages": ["2.5mg", "5mg", "10mg", "20mg"], "category": "ACE Inhibitor", "use": "Hypertension, heart failure"},
    {"name": "Ramipril", "dosages": ["1.25mg", "2.5mg", "5mg", "10mg"], "category": "ACE Inhibitor", "use": "Hypertension, heart protection"},
    {"name": "Hydrochlorothiazide", "dosages": ["12.5mg", "25mg", "50mg"], "category": "Diuretic", "use": "Hypertension, edema"},
    {"name": "Furosemide", "dosages": ["20mg", "40mg", "80mg"], "category": "Loop Diuretic", "use": "Edema, heart failure"},
    {"name": "Spironolactone", "dosages": ["25mg", "50mg", "100mg"], "category": "Diuretic", "use": "Heart failure, edema, PCOS"},
    {"name": "Clopidogrel", "dosages": ["75mg", "150mg"], "category": "Antiplatelet", "use": "Blood clot prevention"},
    {"name": "Warfarin", "dosages": ["1mg", "2mg", "2.5mg", "5mg", "7.5mg", "10mg"], "category": "Anticoagulant", "use": "Blood clot prevention"},
    {"name": "Atorvastatin", "dosages": ["10mg", "20mg", "40mg", "80mg"], "category": "Statin", "use": "High cholesterol"},
    {"name": "Rosuvastatin", "dosages": ["5mg", "10mg", "20mg", "40mg"], "category": "Statin", "use": "High cholesterol"},
    {"name": "Simvastatin", "dosages": ["10mg", "20mg", "40mg"], "category": "Statin", "use": "High cholesterol"},
    {"name": "Nifedipine", "dosages": ["10mg", "20mg", "30mg", "60mg"], "category": "CCB", "use": "Hypertension, angina"},
    {"name": "Verapamil", "dosages": ["40mg", "80mg", "120mg", "240mg"], "category": "CCB", "use": "Hypertension, arrhythmia"},
    {"name": "Digoxin", "dosages": ["0.0625mg", "0.125mg", "0.25mg"], "category": "Cardiac Glycoside", "use": "Heart failure, atrial fibrillation"},
    {"name": "Nitroglycerin", "dosages": ["0.3mg", "0.4mg", "0.6mg"], "category": "Nitrate", "use": "Angina, chest pain"},
    {"name": "Prazosin", "dosages": ["1mg", "2mg", "5mg"], "category": "Alpha Blocker", "use": "Hypertension, PTSD"},

    # ── Respiratory / Allergy ──
    {"name": "Cetirizine", "dosages": ["5mg", "10mg"], "category": "Antihistamine", "use": "Allergies, hay fever"},
    {"name": "Levocetirizine", "dosages": ["2.5mg", "5mg"], "category": "Antihistamine", "use": "Allergies"},
    {"name": "Fexofenadine", "dosages": ["60mg", "120mg", "180mg"], "category": "Antihistamine", "use": "Allergies"},
    {"name": "Loratadine", "dosages": ["5mg", "10mg"], "category": "Antihistamine", "use": "Allergies"},
    {"name": "Chlorpheniramine", "dosages": ["2mg", "4mg"], "category": "Antihistamine", "use": "Allergies, cold symptoms"},
    {"name": "Montelukast", "dosages": ["4mg", "5mg", "10mg"], "category": "Leukotriene Inhibitor", "use": "Asthma, allergies"},
    {"name": "Salbutamol", "dosages": ["2mg", "4mg", "100mcg inhaler"], "category": "Bronchodilator", "use": "Asthma, bronchospasm"},
    {"name": "Budesonide", "dosages": ["0.5mg", "1mg", "200mcg inhaler"], "category": "Corticosteroid", "use": "Asthma, COPD"},
    {"name": "Dextromethorphan", "dosages": ["10mg", "15mg", "30mg"], "category": "Antitussive", "use": "Cough suppressant"},
    {"name": "Guaifenesin", "dosages": ["100mg", "200mg", "400mg"], "category": "Expectorant", "use": "Chest congestion"},
    {"name": "Pseudoephedrine", "dosages": ["30mg", "60mg", "120mg"], "category": "Decongestant", "use": "Nasal congestion"},

    # ── Thyroid ──
    {"name": "Levothyroxine", "dosages": ["12.5mcg", "25mcg", "50mcg", "75mcg", "88mcg", "100mcg", "112mcg", "125mcg", "150mcg", "200mcg"], "category": "Thyroid", "use": "Hypothyroidism"},
    {"name": "Carbimazole", "dosages": ["5mg", "10mg", "20mg"], "category": "Antithyroid", "use": "Hyperthyroidism"},
    {"name": "Propylthiouracil", "dosages": ["50mg", "100mg"], "category": "Antithyroid", "use": "Hyperthyroidism"},

    # ── Neurological / Psychiatric ──
    {"name": "Pregabalin", "dosages": ["25mg", "50mg", "75mg", "100mg", "150mg", "300mg"], "category": "Anticonvulsant", "use": "Neuropathic pain, anxiety"},
    {"name": "Gabapentin", "dosages": ["100mg", "300mg", "400mg", "600mg", "800mg"], "category": "Anticonvulsant", "use": "Neuropathic pain, seizures"},
    {"name": "Carbamazepine", "dosages": ["100mg", "200mg", "400mg"], "category": "Anticonvulsant", "use": "Seizures, bipolar, nerve pain"},
    {"name": "Valproic Acid", "dosages": ["200mg", "250mg", "500mg"], "category": "Anticonvulsant", "use": "Seizures, bipolar, migraine"},
    {"name": "Sertraline", "dosages": ["25mg", "50mg", "100mg"], "category": "SSRI", "use": "Depression, anxiety, OCD"},
    {"name": "Escitalopram", "dosages": ["5mg", "10mg", "20mg"], "category": "SSRI", "use": "Depression, anxiety"},
    {"name": "Fluoxetine", "dosages": ["10mg", "20mg", "40mg", "60mg"], "category": "SSRI", "use": "Depression, OCD, panic"},
    {"name": "Amitriptyline", "dosages": ["10mg", "25mg", "50mg", "75mg"], "category": "TCA", "use": "Depression, neuropathic pain, migraine"},
    {"name": "Clonazepam", "dosages": ["0.25mg", "0.5mg", "1mg", "2mg"], "category": "Benzodiazepine", "use": "Anxiety, seizures, panic"},
    {"name": "Alprazolam", "dosages": ["0.25mg", "0.5mg", "1mg", "2mg"], "category": "Benzodiazepine", "use": "Anxiety, panic disorder"},
    {"name": "Olanzapine", "dosages": ["2.5mg", "5mg", "10mg", "15mg", "20mg"], "category": "Antipsychotic", "use": "Schizophrenia, bipolar"},
    {"name": "Risperidone", "dosages": ["0.5mg", "1mg", "2mg", "3mg", "4mg"], "category": "Antipsychotic", "use": "Schizophrenia, bipolar"},
    {"name": "Quetiapine", "dosages": ["25mg", "50mg", "100mg", "200mg", "300mg"], "category": "Antipsychotic", "use": "Schizophrenia, bipolar, insomnia"},
    {"name": "Lithium Carbonate", "dosages": ["150mg", "300mg", "450mg", "600mg"], "category": "Mood Stabilizer", "use": "Bipolar disorder"},
    {"name": "Zolpidem", "dosages": ["5mg", "10mg"], "category": "Sedative", "use": "Insomnia"},
    {"name": "Melatonin", "dosages": ["1mg", "3mg", "5mg", "10mg"], "category": "Supplement", "use": "Sleep aid"},
    {"name": "Sumatriptan", "dosages": ["25mg", "50mg", "100mg"], "category": "Triptan", "use": "Migraine"},

    # ── Corticosteroids ──
    {"name": "Prednisolone", "dosages": ["5mg", "10mg", "20mg", "40mg"], "category": "Corticosteroid", "use": "Inflammation, autoimmune"},
    {"name": "Dexamethasone", "dosages": ["0.5mg", "0.75mg", "4mg", "6mg"], "category": "Corticosteroid", "use": "Inflammation, severe allergies"},
    {"name": "Methylprednisolone", "dosages": ["4mg", "8mg", "16mg", "32mg"], "category": "Corticosteroid", "use": "Inflammation, autoimmune"},
    {"name": "Hydrocortisone", "dosages": ["5mg", "10mg", "20mg"], "category": "Corticosteroid", "use": "Adrenal insufficiency, inflammation"},

    # ── Vitamins / Supplements ──
    {"name": "Vitamin D3", "dosages": ["400 IU", "1000 IU", "2000 IU", "5000 IU", "60000 IU"], "category": "Supplement", "use": "Vitamin D deficiency"},
    {"name": "Vitamin B12", "dosages": ["500mcg", "1000mcg", "1500mcg"], "category": "Supplement", "use": "B12 deficiency"},
    {"name": "Folic Acid", "dosages": ["400mcg", "1mg", "5mg"], "category": "Supplement", "use": "Folate deficiency, pregnancy"},
    {"name": "Iron (Ferrous Sulfate)", "dosages": ["65mg", "200mg", "325mg"], "category": "Supplement", "use": "Iron deficiency anemia"},
    {"name": "Calcium Carbonate", "dosages": ["500mg", "600mg", "1000mg", "1250mg"], "category": "Supplement", "use": "Calcium deficiency, bone health"},
    {"name": "Zinc", "dosages": ["10mg", "15mg", "20mg", "50mg"], "category": "Supplement", "use": "Immune support, zinc deficiency"},
    {"name": "Magnesium Oxide", "dosages": ["200mg", "250mg", "400mg", "500mg"], "category": "Supplement", "use": "Magnesium deficiency, muscle cramps"},
    {"name": "Omega-3 Fish Oil", "dosages": ["500mg", "1000mg", "2000mg"], "category": "Supplement", "use": "Heart health, triglycerides"},
    {"name": "Multivitamin", "dosages": ["1 tablet"], "category": "Supplement", "use": "General nutrition"},

    # ── Muscle Relaxants ──
    {"name": "Cyclobenzaprine", "dosages": ["5mg", "10mg"], "category": "Muscle Relaxant", "use": "Muscle spasms"},
    {"name": "Tizanidine", "dosages": ["2mg", "4mg", "6mg"], "category": "Muscle Relaxant", "use": "Muscle spasms, spasticity"},
    {"name": "Baclofen", "dosages": ["5mg", "10mg", "20mg"], "category": "Muscle Relaxant", "use": "Muscle spasticity"},
    {"name": "Chlorzoxazone", "dosages": ["250mg", "500mg"], "category": "Muscle Relaxant", "use": "Muscle spasms"},

    # ── Antifungal ──
    {"name": "Fluconazole", "dosages": ["50mg", "100mg", "150mg", "200mg"], "category": "Antifungal", "use": "Fungal infections, candidiasis"},
    {"name": "Clotrimazole", "dosages": ["100mg", "200mg", "500mg"], "category": "Antifungal", "use": "Fungal skin/vaginal infections"},
    {"name": "Itraconazole", "dosages": ["100mg", "200mg"], "category": "Antifungal", "use": "Fungal infections"},
    {"name": "Terbinafine", "dosages": ["250mg"], "category": "Antifungal", "use": "Fungal nail/skin infections"},

    # ── Gout ──
    {"name": "Allopurinol", "dosages": ["100mg", "200mg", "300mg"], "category": "Urate Lowering", "use": "Gout, high uric acid"},
    {"name": "Febuxostat", "dosages": ["40mg", "80mg"], "category": "Urate Lowering", "use": "Gout, hyperuricemia"},
    {"name": "Colchicine", "dosages": ["0.5mg", "0.6mg"], "category": "Gout", "use": "Gout attacks"},

    # ── Others ──
    {"name": "Sildenafil", "dosages": ["25mg", "50mg", "100mg"], "category": "PDE5 Inhibitor", "use": "Erectile dysfunction, PAH"},
    {"name": "Tamsulosin", "dosages": ["0.2mg", "0.4mg"], "category": "Alpha Blocker", "use": "BPH, urinary retention"},
    {"name": "Finasteride", "dosages": ["1mg", "5mg"], "category": "5-Alpha Reductase Inhibitor", "use": "BPH, hair loss"},
    {"name": "Isotretinoin", "dosages": ["10mg", "20mg", "40mg"], "category": "Retinoid", "use": "Severe acne"},
    {"name": "Minoxidil", "dosages": ["2.5mg", "5mg", "10mg"], "category": "Vasodilator", "use": "Hypertension, hair loss"},
    {"name": "Methotrexate", "dosages": ["2.5mg", "5mg", "7.5mg", "10mg", "15mg"], "category": "Immunosuppressant", "use": "Rheumatoid arthritis, psoriasis"},
    {"name": "Hydroxychloroquine", "dosages": ["200mg", "400mg"], "category": "DMARD", "use": "Lupus, rheumatoid arthritis"},
]

# Quick-lookup helper for medicine search
def search_medicines(query: str, limit: int = 10) -> list:
    """Search medicines by name prefix/substring. Returns matches with dosage variants."""
    if not query or len(query) < 1:
        return []
    q = query.lower()
    results = []
    for med in MEDICINE_CATALOG:
        if med["name"].lower().startswith(q) or q in med["name"].lower():
            for dose in med["dosages"]:
                results.append({
                    "name": med["name"],
                    "display": f"{med['name']} {dose}",
                    "dosage": dose,
                    "category": med["category"],
                    "use": med["use"],
                })
    # Sort: prefix matches first, then alphabetical
    results.sort(key=lambda x: (0 if x["name"].lower().startswith(q) else 1, x["name"].lower(), x["dosage"]))
    return results[:limit]


def _is_abnormal(value_str, normal_range: str) -> bool:
    """Check if a value falls outside normal range."""
    if not normal_range or not value_str:
        return False
    try:
        val = float(value_str)
    except (ValueError, TypeError):
        # Qualitative: "Positive" vs expected "Negative"
        v = str(value_str).strip().lower()
        nr = normal_range.strip().lower()
        if nr == "negative" and v not in ("negative", "nil", "absent", "not detected"):
            return True
        if nr == "absent" and v not in ("absent", "nil", "none"):
            return True
        return False
    
    nr = normal_range.strip()
    if nr.startswith("<"):
        try:
            return val >= float(nr[1:])
        except ValueError:
            return False
    elif nr.startswith(">"):
        try:
            return val <= float(nr[1:])
        except ValueError:
            return False
    elif "-" in nr:
        parts = nr.split("-")
        try:
            lo, hi = float(parts[0]), float(parts[1])
            return val < lo or val > hi
        except (ValueError, IndexError):
            return False
    return False


def _score_grade(score):
    if score is None:
        return "N/A"
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Poor"
    return "Critical"


# ══════════════════════════════════════════════════════════════════
#  AGE/GENDER-SPECIFIC NORMAL RANGES
# ══════════════════════════════════════════════════════════════════
# Keys: test_name → list of { "group": str, "range": str, "match": callable }
# Groups are checked in order; first match wins. Fallback to default catalog range.

AGE_GENDER_RANGES = {
    "hemoglobin": [
        {"group": "elderly_male",  "range": "12.0-17.0", "match": lambda age, gender: gender == "male" and age and age >= 65},
        {"group": "elderly_female","range": "11.5-15.0","match": lambda age, gender: gender == "female" and age and age >= 65},
        {"group": "male_adult",   "range": "13.5-17.5", "match": lambda age, gender: gender == "male" and age and age >= 18},
        {"group": "female_adult", "range": "12.0-15.5", "match": lambda age, gender: gender == "female" and age and age >= 18},
        {"group": "child",        "range": "11.0-13.5", "match": lambda age, gender: age is not None and age < 18},
    ],
    "hematocrit": [
        {"group": "male",   "range": "40-54", "match": lambda age, gender: gender == "male"},
        {"group": "female", "range": "36-48", "match": lambda age, gender: gender == "female"},
    ],
    "rbc_count": [
        {"group": "male",   "range": "4.7-6.1", "match": lambda age, gender: gender == "male"},
        {"group": "female", "range": "4.2-5.4", "match": lambda age, gender: gender == "female"},
    ],
    "creatinine": [
        {"group": "male",   "range": "0.7-1.3", "match": lambda age, gender: gender == "male"},
        {"group": "female", "range": "0.6-1.1", "match": lambda age, gender: gender == "female"},
        {"group": "child",  "range": "0.3-0.7", "match": lambda age, gender: age is not None and age < 18},
    ],
    "uric_acid": [
        {"group": "male",   "range": "3.4-7.0", "match": lambda age, gender: gender == "male"},
        {"group": "female", "range": "2.4-6.0", "match": lambda age, gender: gender == "female"},
    ],
    "ferritin": [
        {"group": "male",   "range": "20-500",  "match": lambda age, gender: gender == "male"},
        {"group": "female", "range": "12-150",  "match": lambda age, gender: gender == "female"},
        {"group": "child",  "range": "7-140",   "match": lambda age, gender: age is not None and age < 18},
    ],
    "esr": [
        {"group": "male_young",   "range": "0-15",  "match": lambda age, gender: gender == "male" and age and age < 50},
        {"group": "male_old",     "range": "0-20",  "match": lambda age, gender: gender == "male" and age and age >= 50},
        {"group": "female_young", "range": "0-20",  "match": lambda age, gender: gender == "female" and age and age < 50},
        {"group": "female_old",   "range": "0-30",  "match": lambda age, gender: gender == "female" and age and age >= 50},
    ],
    "alkaline_phosphatase": [
        {"group": "adult",  "range": "44-147", "match": lambda age, gender: age is None or age >= 18},
        {"group": "child",  "range": "150-420","match": lambda age, gender: age is not None and age < 18},
    ],
    "tsh": [
        {"group": "adult",        "range": "0.4-4.0",  "match": lambda age, gender: age is None or age < 65},
        {"group": "elderly",      "range": "0.4-7.0",  "match": lambda age, gender: age is not None and age >= 65},
    ],
    "total_cholesterol": [
        {"group": "adult",  "range": "<200",  "match": lambda age, gender: age is None or age >= 20},
        {"group": "child",  "range": "<170",  "match": lambda age, gender: age is not None and age < 20},
    ],
    "bnp": [
        {"group": "adult",   "range": "<100",  "match": lambda age, gender: age is None or age < 75},
        {"group": "elderly", "range": "<300",  "match": lambda age, gender: age is not None and age >= 75},
    ],
}


def get_normal_range(test_name: str, age: int = None, gender: str = None) -> str:
    """Get the appropriate normal range for a test based on age and gender.
    Falls back to the default catalog range if no specific match."""
    gender_lower = (gender or "").lower().strip()
    if gender_lower in ("m", "male"):
        gender_lower = "male"
    elif gender_lower in ("f", "female"):
        gender_lower = "female"

    if test_name in AGE_GENDER_RANGES:
        for entry in AGE_GENDER_RANGES[test_name]:
            if entry["match"](age, gender_lower):
                return entry["range"]

    # Fallback to catalog default
    catalog_entry = LAB_CATALOG_MAP.get(test_name)
    if catalog_entry:
        return catalog_entry.get("normal_range", "")
    return ""


# ══════════════════════════════════════════════════════════════════
#  LAB INTERPRETATION RULE ENGINE
# ══════════════════════════════════════════════════════════════════
# Each rule: test_name → list of { condition, range/check, severity, interpretation }

LAB_INTERPRETATION_RULES = {
    # ── Hemoglobin / Anemia ──
    "hemoglobin": [
        {"condition": "Severe Anemia",    "check": lambda v: v < 7,         "severity": "critical", "action": "Urgent blood transfusion may be needed. See hematologist immediately."},
        {"condition": "Moderate Anemia",  "check": lambda v: 7 <= v < 10,   "severity": "high",     "action": "Iron studies, B12, folate needed. May need treatment."},
        {"condition": "Mild Anemia",      "check": lambda v: 10 <= v < 12,  "severity": "moderate", "action": "Diet modification, iron supplementation. Recheck in 4-6 weeks."},
        {"condition": "Polycythemia",     "check": lambda v: v > 18,        "severity": "high",     "action": "Risk of clotting. Rule out polycythemia vera."},
    ],
    # ── Blood Sugar ──
    "fasting_glucose": [
        {"condition": "Hypoglycemia",       "check": lambda v: v < 70,          "severity": "high",     "action": "Eat something immediately. If recurrent, evaluate for insulinoma."},
        {"condition": "Pre-diabetic",       "check": lambda v: 100 <= v < 126,  "severity": "moderate", "action": "Lifestyle changes: diet, exercise. Recheck HbA1c in 3 months."},
        {"condition": "Diabetes (fasting)", "check": lambda v: v >= 126,        "severity": "high",     "action": "Confirm with HbA1c. Start diabetes management plan."},
    ],
    "hba1c": [
        {"condition": "Pre-diabetic",        "check": lambda v: 5.7 <= v < 6.5, "severity": "moderate", "action": "Lifestyle intervention. Recheck in 3 months."},
        {"condition": "Diabetes",            "check": lambda v: 6.5 <= v < 8.0, "severity": "high",     "action": "Diabetes confirmed. Start/adjust medication."},
        {"condition": "Uncontrolled Diabetes","check": lambda v: v >= 8.0,       "severity": "critical", "action": "Poor control. Risk of complications. Urgent medication review."},
    ],
    "pp_glucose": [
        {"condition": "Impaired Glucose Tolerance", "check": lambda v: 140 <= v < 200, "severity": "moderate", "action": "Pre-diabetic range post-meal. Dietary counseling needed."},
        {"condition": "Diabetes (post-meal)",       "check": lambda v: v >= 200,        "severity": "high",     "action": "Confirms diabetes. Coordinate with HbA1c."},
    ],
    # ── Kidney Function ──
    "creatinine": [
        {"condition": "Elevated Creatinine", "check": lambda v: v > 1.3, "severity": "moderate", "action": "Assess kidney function with eGFR. Check hydration status."},
        {"condition": "High Creatinine",     "check": lambda v: v > 2.0, "severity": "high",     "action": "Possible kidney impairment. Nephrology referral needed."},
        {"condition": "Critically High",     "check": lambda v: v > 4.0, "severity": "critical", "action": "Kidney failure risk. Urgent nephrology consultation."},
    ],
    "egfr": [
        {"condition": "CKD Stage 2",  "check": lambda v: 60 <= v < 90,  "severity": "low",      "action": "Mild kidney damage. Monitor annually."}, 
        {"condition": "CKD Stage 3a", "check": lambda v: 45 <= v < 60,  "severity": "moderate", "action": "Moderate decline. Nephrology referral recommended."},
        {"condition": "CKD Stage 3b", "check": lambda v: 30 <= v < 45,  "severity": "high",     "action": "Significant decline. Active nephrology management."},
        {"condition": "CKD Stage 4",  "check": lambda v: 15 <= v < 30,  "severity": "high",     "action": "Severe decline. Prepare for dialysis discussion."},
        {"condition": "CKD Stage 5",  "check": lambda v: v < 15,        "severity": "critical", "action": "Kidney failure. Dialysis or transplant evaluation."},
    ],
    "potassium": [
        {"condition": "Hypokalemia",     "check": lambda v: v < 3.5,  "severity": "high",     "action": "Risk of arrhythmia. Supplement urgently."},
        {"condition": "Severe Hypokalemia","check": lambda v: v < 2.5, "severity": "critical", "action": "Life-threatening. IV potassium needed immediately."},
        {"condition": "Hyperkalemia",     "check": lambda v: v > 5.0,  "severity": "high",     "action": "ECG monitoring. Check medication side effects (ACE inhibitors, K-sparing diuretics)."},
        {"condition": "Severe Hyperkalemia","check": lambda v: v > 6.0,"severity": "critical", "action": "Cardiac risk. Emergency treatment needed."},
    ],
    # ── Liver ──
    "sgpt_alt": [
        {"condition": "Mildly Elevated ALT",   "check": lambda v: 56 < v <= 150,  "severity": "moderate", "action": "Possible fatty liver or medication effect. Check alcohol use."},
        {"condition": "Significantly Elevated", "check": lambda v: 150 < v <= 500, "severity": "high",     "action": "Active liver injury. Rule out hepatitis, drugs, alcohol."},
        {"condition": "Severely Elevated",      "check": lambda v: v > 500,        "severity": "critical", "action": "Acute liver damage. Urgent hepatology referral."},
    ],
    "total_bilirubin": [
        {"condition": "Mild Jaundice",   "check": lambda v: 1.2 < v <= 3.0, "severity": "moderate", "action": "Investigate: hemolysis, Gilbert's syndrome, liver disease."},
        {"condition": "Severe Jaundice", "check": lambda v: v > 3.0,         "severity": "high",     "action": "Obstructive vs hepatocellular cause. Imaging needed."},
    ],
    # ── Lipids ──
    "ldl_cholesterol": [
        {"condition": "Borderline High LDL", "check": lambda v: 100 <= v < 130, "severity": "low",      "action": "Lifestyle changes: diet, exercise."},
        {"condition": "High LDL",            "check": lambda v: 130 <= v < 160, "severity": "moderate", "action": "Cardiovascular risk elevated. Consider statin therapy."},
        {"condition": "Very High LDL",       "check": lambda v: v >= 160,       "severity": "high",     "action": "Strong statin indication. Check family history of heart disease."},
    ],
    "triglycerides": [
        {"condition": "Borderline High TG",  "check": lambda v: 150 <= v < 200, "severity": "low",      "action": "Reduce sugar, alcohol, refined carbs."},
        {"condition": "High Triglycerides",  "check": lambda v: 200 <= v < 500, "severity": "moderate", "action": "Pancreatitis risk. Medication may be needed."},
        {"condition": "Very High TG",        "check": lambda v: v >= 500,       "severity": "high",     "action": "High pancreatitis risk. Urgent lipid management."},
    ],
    # ── Thyroid ──
    "tsh": [
        {"condition": "Hyperthyroidism",       "check": lambda v: v < 0.4,  "severity": "moderate", "action": "Check Free T3/T4. Possible Graves' disease or toxic nodule."},
        {"condition": "Subclinical Hypothyroid","check": lambda v: 4.0 < v <= 10.0, "severity": "low", "action": "Recheck in 6-8 weeks. May not need treatment."},
        {"condition": "Hypothyroidism",        "check": lambda v: v > 10.0, "severity": "moderate", "action": "Start levothyroxine. Check TPO antibodies."},
    ],
    # ── Cardiac ──
    "troponin_i": [
        {"condition": "Elevated Troponin",    "check": lambda v: v >= 0.04, "severity": "critical", "action": "Possible myocardial injury/infarction. URGENT cardiology."},
    ],
    "bnp": [
        {"condition": "Possible Heart Failure","check": lambda v: v >= 100,  "severity": "high",     "action": "Heart failure likely. Echo needed. Cardiology referral."},
        {"condition": "Severe Heart Failure",  "check": lambda v: v >= 400,  "severity": "critical", "action": "Advanced heart failure. Urgent management needed."},
    ],
    # ── Iron ──
    "ferritin": [
        {"condition": "Iron Deficiency",     "check": lambda v: v < 12,  "severity": "moderate", "action": "Iron supplementation needed. Check for bleeding source."},
        {"condition": "Iron Overload",       "check": lambda v: v > 500, "severity": "high",     "action": "Rule out hemochromatosis. Genetic testing may be needed."},
    ],
    # ── Vitamins ──
    "vitamin_d": [
        {"condition": "Severe Vit D Deficiency","check": lambda v: v < 10,       "severity": "high",     "action": "High-dose supplementation (60,000 IU/week). Recheck in 3 months."},
        {"condition": "Vit D Deficiency",       "check": lambda v: 10 <= v < 20, "severity": "moderate", "action": "Supplement 1000-2000 IU daily. Sun exposure."},
        {"condition": "Vit D Insufficient",     "check": lambda v: 20 <= v < 30, "severity": "low",      "action": "Mild supplementation: 600-1000 IU daily."},
    ],
    "vitamin_b12": [
        {"condition": "B12 Deficiency",  "check": lambda v: v < 200, "severity": "moderate", "action": "Supplement B12. Check for pernicious anemia if severe."},
        {"condition": "Low B12",         "check": lambda v: 200 <= v < 300, "severity": "low", "action": "Borderline. Consider supplementation."},
    ],
    # ── WBC ──
    "wbc_count": [
        {"condition": "Leukopenia",   "check": lambda v: v < 4000,  "severity": "moderate", "action": "Infection risk. Check medication effects, viral causes."},
        {"condition": "Leukocytosis", "check": lambda v: v > 11000, "severity": "moderate", "action": "Active infection or inflammation likely. Investigate cause."},
        {"condition": "Severe Leukocytosis","check": lambda v: v > 20000,"severity": "high","action": "Significant infection or hematologic disorder. Urgent workup."},
    ],
    "platelet_count": [
        {"condition": "Thrombocytopenia",  "check": lambda v: v < 1.5,  "severity": "high",     "action": "Bleeding risk. Check cause: drugs, infection, autoimmune."},
        {"condition": "Severe Thrombocytopenia","check": lambda v: v < 0.5,"severity": "critical","action": "Spontaneous bleeding risk. Urgent hematology."},
        {"condition": "Thrombocytosis",    "check": lambda v: v > 4.0,  "severity": "moderate", "action": "Clotting risk. Check iron deficiency, inflammation, myeloproliferative disorder."},
    ],
}


def interpret_lab_value(test_name: str, value_str, age: int = None, gender: str = None) -> Dict:
    """
    Interpret a single lab value.
    Returns: {
      test_name, value, normal_range, is_abnormal, 
      interpretations: [{condition, severity, action, reasoning}]
    }
    """
    result = {
        "test_name": test_name,
        "value": value_str,
        "normal_range": "",
        "is_abnormal": False,
        "interpretations": [],
    }

    # Get age/gender-specific normal range
    normal_range = get_normal_range(test_name, age, gender)
    result["normal_range"] = normal_range

    try:
        val = float(value_str)
    except (ValueError, TypeError):
        # Qualitative value — just check abnormality
        result["is_abnormal"] = _is_abnormal(value_str, normal_range)
        return result

    result["is_abnormal"] = _is_abnormal(value_str, normal_range)

    # Run interpretation rules
    rules = LAB_INTERPRETATION_RULES.get(test_name, [])
    for rule in rules:
        if rule["check"](val):
            result["interpretations"].append({
                "condition": rule["condition"],
                "severity": rule["severity"],
                "action": rule["action"],
                "reasoning": f"{test_name} = {val} → {rule['condition']}",
            })

    return result


def interpret_lab_panel(lab_values: Dict, age: int = None, gender: str = None) -> Dict:
    """
    Interpret a full panel of lab results.
    lab_values: {test_name: value_str, ...}
    Returns: {
      results: [{test_name, value, normal_range, is_abnormal, interpretations}],
      summary: { critical: [...], high: [...], moderate: [...], low: [...] },
      overall_assessment: str
    }
    """
    results = []
    summary = {"critical": [], "high": [], "moderate": [], "low": []}

    for test_name, value_str in lab_values.items():
        interp = interpret_lab_value(test_name, value_str, age, gender)
        results.append(interp)
        for finding in interp["interpretations"]:
            sev = finding["severity"]
            if sev in summary:
                summary[sev].append({
                    "test": test_name,
                    "condition": finding["condition"],
                    "action": finding["action"],
                    "reasoning": finding["reasoning"],
                })

    # Overall assessment
    if summary["critical"]:
        overall = "CRITICAL — Immediate medical attention required for: " + ", ".join(
            f["condition"] for f in summary["critical"]
        )
    elif summary["high"]:
        overall = "ATTENTION NEEDED — Significant findings: " + ", ".join(
            f["condition"] for f in summary["high"]
        )
    elif summary["moderate"]:
        overall = "MONITOR — Some values need follow-up: " + ", ".join(
            f["condition"] for f in summary["moderate"]
        )
    elif summary["low"]:
        overall = "GOOD — Minor observations: " + ", ".join(
            f["condition"] for f in summary["low"]
        )
    else:
        overall = "NORMAL — All values within expected ranges."

    return {
        "results": results,
        "summary": summary,
        "overall_assessment": overall,
    }
