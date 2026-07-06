"""
Predictive Health Trajectory System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Novel algorithm that analyzes temporal patterns across ALL patient data:
  - Lab result trajectories (rate of change, acceleration, projection)
  - Medication correlation (did Drug X affect Lab Y?)
  - Symptom frequency from chat history
  - Body map event density
  - Intervention window calculation (how long until critical?)

This is NOT a snapshot. It's a TIME-SERIES analysis that predicts WHERE
your health values are HEADING, not just where they ARE.
"""

import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from utils.utils_logger import setup_logger

logger = setup_logger(__name__)

# ── Critical thresholds for common lab tests ────────────────────
# Format: test_name → (critical_low, low, high, critical_high, unit)
CRITICAL_THRESHOLDS = {
    "hemoglobin":             (5.0,  10.0, 17.5, 20.0, "g/dL"),
    "blood_sugar":            (40,   70,   140,  400,   "mg/dL"),
    "fasting_glucose":        (40,   70,   126,  400,   "mg/dL"),
    "random_glucose":         (40,   70,   200,  500,   "mg/dL"),
    "hba1c":                  (3.0,  4.0,  6.5,  14.0,  "%"),
    "total_cholesterol":      (80,   120,  200,  350,   "mg/dL"),
    "ldl_cholesterol":        (30,   50,   130,  250,   "mg/dL"),
    "hdl_cholesterol":        (15,   40,   90,   120,   "mg/dL"),
    "triglycerides":          (30,   50,   150,  500,   "mg/dL"),
    "creatinine":             (0.2,  0.5,  1.3,  10.0,  "mg/dL"),
    "blood_urea":             (5,    7,    20,   100,   "mg/dL"),
    "uric_acid":              (1.0,  2.5,  7.0,  15.0,  "mg/dL"),
    "sgot":                   (5,    10,   40,   1000,  "U/L"),
    "sgpt":                   (5,    7,    56,   1000,  "U/L"),
    "tsh":                    (0.1,  0.4,  4.0,  100,   "mIU/L"),
    "vitamin_d":              (5,    20,   50,   150,   "ng/mL"),
    "vitamin_b12":            (100,  200,  900,  2000,  "pg/mL"),
    "iron":                   (20,   60,   170,  350,   "μg/dL"),
    "ferritin":               (5,    20,   300,  1000,  "ng/mL"),
    "platelets":              (50,   150,  400,  1000,  "×10³/μL"),
    "wbc":                    (1.0,  4.0,  11.0, 50.0,  "×10³/μL"),
    "rbc":                    (2.0,  4.0,  6.0,  8.0,   "×10⁶/μL"),
    "systolic_bp":            (60,   90,   130,  200,   "mmHg"),
    "diastolic_bp":           (40,   60,   85,   130,   "mmHg"),
    "heart_rate":             (30,   60,   100,  200,   "bpm"),
}

# How many data points needed before trajectory is meaningful
MIN_DATA_POINTS = 2
# Minimum days between first and last reading
MIN_TIMESPAN_DAYS = 3


def _parse_numeric(value_str: str) -> Optional[float]:
    """Extract numeric value from lab result string."""
    if not value_str:
        return None
    try:
        # Handle values like "126.5", "5.7%", "< 200", "> 3.0"
        cleaned = re.sub(r'[<>≤≥~%,\s]', '', str(value_str))
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_range(range_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse normal range string like '70-110' or '4.0 - 6.5'."""
    if not range_str:
        return None, None
    try:
        parts = re.split(r'[-–—~]', range_str.strip())
        if len(parts) == 2:
            lo = _parse_numeric(parts[0])
            hi = _parse_numeric(parts[1])
            return lo, hi
    except Exception:
        pass
    return None, None


def _linear_regression(points: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    """
    Simple linear regression.
    points: list of (x, y) — where x = days from first reading, y = value
    Returns: (slope, intercept, r_squared)
    """
    n = len(points)
    if n < 2:
        return 0.0, points[0][1] if points else 0.0, 0.0

    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)

    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-10:
        return 0.0, sum_y / n, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R² (coefficient of determination)
    mean_y = sum_y / n
    ss_tot = sum((p[1] - mean_y) ** 2 for p in points)
    ss_res = sum((p[1] - (slope * p[0] + intercept)) ** 2 for p in points)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return slope, intercept, r_squared


class PredictiveHealthEngine:
    """
    Analyzes temporal health data to predict trajectories and generate alerts.

    Novel features:
    1. Rate-of-change analysis (not just "is this high?" but "how fast is it rising?")
    2. Intervention window prediction (how long before a value becomes critical?)
    3. Medication-lab correlation (did starting Drug X improve Lab Y?)
    4. Multi-signal anomaly detection (combining labs + symptoms + medications)
    """

    def __init__(self, db):
        """
        Args:
            db: HealthDatabase instance
        """
        self.db = db
        logger.info("PredictiveHealthEngine initialized")

    def analyze_lab_trajectory(self, patient_id: str, test_name: str) -> Optional[Dict]:
        """
        Analyze a single lab test's trajectory over time.

        Returns rate of change, trend direction, acceleration,
        projected future values, and intervention window.
        """
        results = self.db.get_lab_results(patient_id, test_name=test_name, limit=50)
        if len(results) < MIN_DATA_POINTS:
            return None

        # Parse dates and values
        data_points = []
        for r in reversed(results):  # oldest first
            val = _parse_numeric(r.get("value"))
            if val is None:
                continue
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            data_points.append({"date": dt, "value": val, "raw": r})

        if len(data_points) < MIN_DATA_POINTS:
            return None

        first_date = data_points[0]["date"]
        last_date = data_points[-1]["date"]
        timespan_days = (last_date - first_date).days

        if timespan_days < MIN_TIMESPAN_DAYS:
            return None

        # Convert to regression format: (days_from_start, value)
        reg_points = [
            ((dp["date"] - first_date).days, dp["value"])
            for dp in data_points
        ]

        slope, intercept, r_squared = _linear_regression(reg_points)

        # Current (latest) and first values
        latest_val = data_points[-1]["value"]
        first_val = data_points[0]["value"]
        total_change = latest_val - first_val
        pct_change = (total_change / first_val * 100) if first_val != 0 else 0

        # Slope per month (30 days)
        slope_per_month = slope * 30

        # Trend direction
        if abs(slope_per_month) < 0.5 and abs(pct_change) < 3:
            trend = "stable"
        elif slope > 0:
            trend = "rising"
        else:
            trend = "falling"

        # Acceleration: compare first half slope vs second half slope
        mid = len(reg_points) // 2
        acceleration = "steady"
        if len(reg_points) >= 4:
            slope_first, _, _ = _linear_regression(reg_points[:mid])
            slope_second, _, _ = _linear_regression(reg_points[mid:])
            accel_ratio = slope_second / slope_first if abs(slope_first) > 0.001 else 0
            if accel_ratio > 1.5:
                acceleration = "accelerating"
            elif accel_ratio < 0.5 and accel_ratio > 0:
                acceleration = "decelerating"
            elif slope_first > 0 and slope_second < 0:
                acceleration = "reversing_down"
            elif slope_first < 0 and slope_second > 0:
                acceleration = "reversing_up"

        # Future projections
        today_days = (datetime.now() - first_date).days
        projected = {}
        for months_ahead in [3, 6, 12]:
            future_days = today_days + months_ahead * 30
            proj_value = slope * future_days + intercept
            projected[f"{months_ahead}m"] = round(proj_value, 1)

        # Intervention window: how many days until critical threshold?
        thresholds = CRITICAL_THRESHOLDS.get(test_name)
        intervention_window = None
        critical_direction = None

        if thresholds and abs(slope) > 0.0001:
            _, range_low, range_high, critical_high, _ = thresholds
            # Normal range from our data if available
            if data_points[-1]["raw"].get("normal_range"):
                range_low_p, range_high_p = _parse_range(data_points[-1]["raw"]["normal_range"])
                if range_low_p is not None:
                    range_low = range_low_p
                if range_high_p is not None:
                    range_high = range_high_p

            if slope > 0 and latest_val < range_high:
                # Rising toward upper limit
                days_to_high = (range_high - latest_val) / slope
                intervention_window = max(0, int(days_to_high))
                critical_direction = "approaching_high"
            elif slope < 0 and latest_val > range_low:
                # Falling toward lower limit
                days_to_low = (latest_val - range_low) / abs(slope)
                intervention_window = max(0, int(days_to_low))
                critical_direction = "approaching_low"

        # Severity assessment
        severity = "normal"
        if thresholds:
            crit_lo, low, high, crit_hi, _ = thresholds
            if latest_val <= crit_lo or latest_val >= crit_hi:
                severity = "critical"
            elif latest_val < low or latest_val > high:
                severity = "abnormal"
            elif trend != "stable" and acceleration == "accelerating":
                severity = "warning"
            elif trend != "stable":
                severity = "watch"

        return {
            "test_name": test_name,
            "data_points": len(data_points),
            "timespan_days": timespan_days,
            "first_value": round(first_val, 1),
            "latest_value": round(latest_val, 1),
            "total_change": round(total_change, 1),
            "percent_change": round(pct_change, 1),
            "trend": trend,
            "slope_per_month": round(slope_per_month, 2),
            "acceleration": acceleration,
            "r_squared": round(r_squared, 3),
            "projected": projected,
            "intervention_window_days": intervention_window,
            "critical_direction": critical_direction,
            "severity": severity,
            "unit": thresholds[4] if thresholds else data_points[-1]["raw"].get("unit", ""),
        }

    def detect_medication_correlations(self, patient_id: str) -> List[Dict]:
        """
        Cross-reference medication start/stop dates with lab value changes.

        Detects patterns like:
        - "After starting Metformin, blood sugar dropped 15% over 2 months"
        - "Since stopping Atorvastatin, cholesterol has risen 22%"
        """
        medications = self.db.get_medications(patient_id, active_only=False)
        if not medications:
            return []

        all_labs = self.db.get_lab_results(patient_id, limit=200)
        if not all_labs:
            return []

        # Group lab results by test name with dates
        lab_by_test = defaultdict(list)
        for lab in all_labs:
            val = _parse_numeric(lab.get("value"))
            if val is not None and lab.get("date"):
                try:
                    dt = datetime.strptime(lab["date"], "%Y-%m-%d")
                    lab_by_test[lab["test_name"]].append({"date": dt, "value": val})
                except ValueError:
                    pass

        correlations = []

        for med in medications:
            if not med.get("start_date"):
                continue
            try:
                med_start = datetime.strptime(med["start_date"], "%Y-%m-%d")
            except ValueError:
                continue

            med_end = None
            if med.get("end_date"):
                try:
                    med_end = datetime.strptime(med["end_date"], "%Y-%m-%d")
                except ValueError:
                    pass

            # Check each lab test for changes around medication start/stop
            for test_name, readings in lab_by_test.items():
                sorted_readings = sorted(readings, key=lambda x: x["date"])

                # Labs BEFORE medication (30 days before start)
                before = [r for r in sorted_readings
                          if med_start - timedelta(days=60) <= r["date"] < med_start]
                # Labs AFTER medication (30-120 days after start)
                after = [r for r in sorted_readings
                         if med_start + timedelta(days=14) <= r["date"] <= med_start + timedelta(days=180)]

                if before and after:
                    avg_before = sum(r["value"] for r in before) / len(before)
                    avg_after = sum(r["value"] for r in after) / len(after)
                    change = avg_after - avg_before
                    pct = (change / avg_before * 100) if avg_before != 0 else 0

                    # Only report meaningful changes (>5%)
                    if abs(pct) > 5:
                        correlations.append({
                            "medication": med["name"],
                            "dosage": med.get("dosage", ""),
                            "test_name": test_name,
                            "event": "started",
                            "avg_before": round(avg_before, 1),
                            "avg_after": round(avg_after, 1),
                            "change": round(change, 1),
                            "percent_change": round(pct, 1),
                            "direction": "improved" if (
                                (test_name in ["blood_sugar", "hba1c", "total_cholesterol",
                                               "ldl_cholesterol", "triglycerides", "creatinine",
                                               "sgot", "sgpt", "uric_acid"] and change < 0) or
                                (test_name in ["hemoglobin", "vitamin_d", "vitamin_b12",
                                               "hdl_cholesterol", "iron"] and change > 0)
                            ) else "worsened" if abs(pct) > 10 else "changed",
                            "confidence": "high" if len(before) >= 2 and len(after) >= 2 else "moderate",
                        })

        # Sort by absolute percent change (most significant first)
        correlations.sort(key=lambda x: abs(x["percent_change"]), reverse=True)
        return correlations

    def extract_symptom_frequency(self, patient_id: str) -> Dict:
        """
        Analyze past chat messages to detect symptom mention frequency.

        Scans user messages for common symptom keywords and tracks how
        often they appear over time.
        """
        SYMPTOM_KEYWORDS = [
            "headache", "fever", "cough", "pain", "nausea", "vomit",
            "diarrhea", "fatigue", "tired", "dizzy", "breathless",
            "chest pain", "swelling", "rash", "itching", "insomnia",
            "anxiety", "depression", "weight loss", "weight gain",
            "joint pain", "back pain", "stomach pain", "weakness",
            # Hindi symptoms
            "दर्द", "बुखार", "खांसी", "उल्टी", "कमजोरी", "थकान",
            "चक्कर", "सूजन", "सिरदर्द",
        ]

        messages = self.db.get_all_conversations(patient_id, limit=500)
        user_msgs = [m for m in messages if m.get("role") == "user"]

        symptom_counts = defaultdict(lambda: {"count": 0, "dates": []})

        for msg in user_msgs:
            text = (msg.get("content") or "").lower()
            msg_date = msg.get("timestamp", "")
            for symptom in SYMPTOM_KEYWORDS:
                if symptom.lower() in text:
                    symptom_counts[symptom]["count"] += 1
                    symptom_counts[symptom]["dates"].append(msg_date)

        # Convert to sorted list
        result = []
        for symptom, data in symptom_counts.items():
            result.append({
                "symptom": symptom,
                "mentions": data["count"],
                "first_mention": data["dates"][0] if data["dates"] else None,
                "last_mention": data["dates"][-1] if data["dates"] else None,
                "recurring": data["count"] >= 3,
            })

        result.sort(key=lambda x: x["mentions"], reverse=True)
        return {"symptoms": result[:15], "total_messages_analyzed": len(user_msgs)}

    def generate_health_forecast(self, patient_id: str) -> Dict:
        """
        MASTER FUNCTION — generates the complete health trajectory analysis.

        Combines:
        - Lab trajectories for ALL tracked tests
        - Medication correlations
        - Symptom frequency from chat history
        - Body map event density
        - Overall health trajectory alert level
        """
        # 1. Get all unique lab tests for this patient
        all_labs = self.db.get_lab_results(patient_id, limit=500)
        test_names = list(set(r["test_name"] for r in all_labs))

        # 2. Run trajectory analysis on each test
        trajectories = []
        for test_name in test_names:
            traj = self.analyze_lab_trajectory(patient_id, test_name)
            if traj:
                trajectories.append(traj)

        # Sort by severity (worst first)
        severity_order = {"critical": 0, "abnormal": 1, "warning": 2, "watch": 3, "normal": 4}
        trajectories.sort(key=lambda t: severity_order.get(t["severity"], 5))

        # 3. Medication correlations
        med_correlations = self.detect_medication_correlations(patient_id)

        # 4. Symptom frequency
        symptom_data = self.extract_symptom_frequency(patient_id)

        # 5. Body map density
        body_map = self.db.get_body_map(patient_id)
        body_regions_with_activity = len(body_map) if body_map else 0

        # 6. Count active medications
        active_meds = self.db.get_medications(patient_id, active_only=True)

        # 7. Overall alert level — determined by worst trajectory
        alert_level = "green"  # healthy
        alert_message = "All tracked values are stable."
        alert_details = []

        for t in trajectories:
            if t["severity"] == "critical":
                alert_level = "red"
                alert_details.append(
                    f'{t["test_name"].replace("_"," ").title()}: '
                    f'CRITICAL at {t["latest_value"]} {t["unit"]}'
                )
            elif t["severity"] == "abnormal":
                if alert_level not in ("red",):
                    alert_level = "orange"
                alert_details.append(
                    f'{t["test_name"].replace("_"," ").title()}: '
                    f'abnormal ({t["trend"]}, {t["percent_change"]:+.0f}%)'
                )
            elif t["severity"] == "warning":
                if alert_level not in ("red", "orange"):
                    alert_level = "yellow"
                window = t.get("intervention_window_days")
                window_text = f", intervene within {window} days" if window else ""
                alert_details.append(
                    f'{t["test_name"].replace("_"," ").title()}: '
                    f'{t["acceleration"]} {t["trend"]}{window_text}'
                )
            elif t["severity"] == "watch":
                if alert_level == "green":
                    alert_level = "blue"
                alert_details.append(
                    f'{t["test_name"].replace("_"," ").title()}: '
                    f'trending {t["trend"]} ({t["slope_per_month"]:+.1f}/month)'
                )

        if alert_details:
            alert_message = "; ".join(alert_details[:3])
            if len(alert_details) > 3:
                alert_message += f" (+{len(alert_details)-3} more)"

        # 8. Check if we have enough data to show the forecast
        has_sufficient_data = (
            len(trajectories) >= 1 or
            len(med_correlations) >= 1 or
            symptom_data["total_messages_analyzed"] >= 3
        )

        return {
            "patient_id": patient_id,
            "generated_at": datetime.now().isoformat(),
            "has_sufficient_data": has_sufficient_data,

            # Overall alert
            "alert_level": alert_level,   # green/blue/yellow/orange/red
            "alert_message": alert_message,

            # Detailed trajectories
            "trajectories": trajectories,
            "trajectory_count": len(trajectories),

            # Medication effectiveness
            "medication_correlations": med_correlations,

            # Symptom patterns
            "symptom_patterns": symptom_data,

            # Summary stats
            "total_lab_tests_tracked": len(test_names),
            "active_medications": len(active_meds),
            "body_regions_monitored": body_regions_with_activity,

            # Data quality
            "min_data_points_required": MIN_DATA_POINTS,
            "min_timespan_days_required": MIN_TIMESPAN_DAYS,
        }
