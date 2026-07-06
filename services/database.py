"""
Health Records Database
Complete patient health management with SQLite
Tracks: patients, sessions, messages, health events, lab results, images, body map
Sensitive fields encrypted with Fernet symmetric encryption (HIPAA-like protection)
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from utils.utils_logger import setup_logger

logger = setup_logger(__name__)

# ── Field-level encryption for sensitive patient data ───────────
# Key path and database path are configurable so containers can mount persistent volumes.
_ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", os.path.join("data", ".encryption_key"))
_DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "data/health_records.db")
# Fields that must be encrypted at rest
_SENSITIVE_FIELDS = {"name", "allergies", "chronic_conditions", "family_history", "emergency_contact"}


def _get_fernet() -> Fernet:
    """Load or generate the encryption key."""
    if os.path.exists(_ENCRYPTION_KEY_PATH):
        with open(_ENCRYPTION_KEY_PATH, "rb") as f:
            key = f.read().strip()
    else:
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(_ENCRYPTION_KEY_PATH), exist_ok=True)
        with open(_ENCRYPTION_KEY_PATH, "wb") as f:
            f.write(key)
        logger.info("Generated new patient data encryption key")
    return Fernet(key)


_fernet = _get_fernet()


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Encrypt a sensitive field value. Returns base64 token string."""
    if value is None or value == "":
        return value
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """Decrypt a sensitive field value. Returns plain text."""
    if value is None or value == "":
        return value
    try:
        return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # Value is not encrypted (legacy data) — return as-is
        return value


class HealthDatabase:
    """Full health records database — offline SQLite with connection pooling"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # Persistent connection per thread (thread-local storage)
        self._local = threading.local()
        self._init_schema()
        logger.info(f"HealthDatabase ready: {self.db_path} (pooled connections)")

    def _conn(self):
        """Get or create a persistent connection for the current thread."""
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=10000")
            self._local.conn = conn
        return conn

    def _init_schema(self):
        conn = self._conn()
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            blood_group TEXT,
            allergies TEXT,
            chronic_conditions TEXT,
            ethnicity TEXT,
            family_history TEXT,
            emergency_contact TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            summary TEXT,
            triage_level TEXT,
            language TEXT DEFAULT 'en',
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS health_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            body_region TEXT,
            severity TEXT DEFAULT 'mild',
            date TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            date TEXT NOT NULL,
            test_name TEXT NOT NULL,
            value TEXT,
            unit TEXT,
            normal_range TEXT,
            status TEXT,
            source TEXT DEFAULT 'manual',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS medical_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            image_path TEXT NOT NULL,
            image_type TEXT DEFAULT 'photo',
            body_region TEXT,
            description TEXT,
            ai_analysis TEXT,
            date TEXT NOT NULL,
            session_id TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            start_date TEXT,
            end_date TEXT,
            active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS medication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            patient_id TEXT NOT NULL,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'taken',
            FOREIGN KEY (medication_id) REFERENCES medications(id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )""")

        # Indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_msg_patient ON messages(patient_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_patient ON health_events(patient_id, date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_lab_patient ON lab_results(patient_id, date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_img_patient ON medical_images(patient_id, body_region)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_med_patient ON medications(patient_id, active)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_medlog_med ON medication_logs(medication_id, taken_at)")

        # Migration: add ethnicity column if missing
        try:
            c.execute("SELECT ethnicity FROM patients LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE patients ADD COLUMN ethnicity TEXT")

        try:
            c.execute("SELECT family_history FROM patients LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE patients ADD COLUMN family_history TEXT")

        try:
            c.execute("SELECT password_hash FROM patients LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE patients ADD COLUMN password_hash TEXT")

        # Add reminder columns to medications if missing
        try:
            c.execute("SELECT reminder_morning FROM medications LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE medications ADD COLUMN reminder_morning TEXT DEFAULT '08:00'")
            c.execute("ALTER TABLE medications ADD COLUMN reminder_evening TEXT DEFAULT '21:00'")
            c.execute("ALTER TABLE medications ADD COLUMN reminder_enabled INTEGER DEFAULT 0")

        conn.commit()

    # ── Patient Management ──────────────────────────────────────

    def _encrypt_patient_fields(self, data: dict) -> dict:
        """Encrypt sensitive fields before writing to DB."""
        result = dict(data)
        for field in _SENSITIVE_FIELDS:
            if field in result and result[field] is not None:
                result[field] = encrypt_field(result[field])
        return result

    def _decrypt_patient_row(self, row_dict: dict) -> dict:
        """Decrypt sensitive fields after reading from DB."""
        result = dict(row_dict)
        for field in _SENSITIVE_FIELDS:
            if field in result and result[field] is not None:
                result[field] = decrypt_field(result[field])
        return result

    def ensure_patient(self, patient_id: str, name: str = None, password_hash: str = None, **kwargs):
        conn = self._conn()
        row = conn.execute("SELECT patient_id FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        if not row:
            enc_name = encrypt_field(name or patient_id)
            enc_allergies = encrypt_field(kwargs.get("allergies"))
            enc_chronic = encrypt_field(kwargs.get("chronic_conditions"))
            enc_family = encrypt_field(kwargs.get("family_history"))
            conn.execute(
                "INSERT INTO patients (patient_id, name, age, gender, blood_group, allergies, chronic_conditions, ethnicity, family_history, password_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (patient_id, enc_name, kwargs.get("age"), kwargs.get("gender"),
                 kwargs.get("blood_group"), enc_allergies, enc_chronic, kwargs.get("ethnicity"), enc_family, password_hash)
            )
        else:
            updates = {k: v for k, v in kwargs.items() if v is not None and k in ("name","age","gender","blood_group","allergies","chronic_conditions","ethnicity","family_history")}
            if name:
                updates["name"] = name
            if password_hash:
                updates["password_hash"] = password_hash
            if updates:
                # Encrypt sensitive fields before update
                for field in _SENSITIVE_FIELDS:
                    if field in updates and updates[field] is not None:
                        updates[field] = encrypt_field(updates[field])
                set_clause = ", ".join(f"{k}=?" for k in updates)
                conn.execute(f"UPDATE patients SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE patient_id=?",
                             list(updates.values()) + [patient_id])
        conn.commit()

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        if not row:
            return None
        return self._decrypt_patient_row(dict(row))

    def list_patients(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM patients ORDER BY updated_at DESC").fetchall()
        return [self._decrypt_patient_row(dict(r)) for r in rows]

    # ── Session Management ──────────────────────────────────────

    def ensure_session(self, session_id: str, patient_id: str, language: str = "en"):
        self.ensure_patient(patient_id)
        conn = self._conn()
        row = conn.execute("SELECT session_id FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO sessions (session_id, patient_id, language) VALUES (?,?,?)",
                         (session_id, patient_id, language))
            conn.commit()

    def get_sessions(self, patient_id: str) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM sessions WHERE patient_id=? ORDER BY started_at DESC", (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_session(self, session_id: str, **kwargs):
        conn = self._conn()
        allowed = {"summary", "triage_level", "ended_at"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(f"UPDATE sessions SET {set_clause} WHERE session_id=?",
                         list(updates.values()) + [session_id])
            conn.commit()

    def delete_session(self, session_id: str, patient_id: str) -> bool:
        conn = self._conn()
        conn.execute("DELETE FROM messages WHERE session_id=? AND patient_id=?", (session_id, patient_id))
        cur = conn.execute("DELETE FROM sessions WHERE session_id=? AND patient_id=?", (session_id, patient_id))
        conn.commit()
        return cur.rowcount > 0

    # ── Messages ────────────────────────────────────────────────

    def save_message(self, patient_id: str, session_id: str, role: str,
                     content: str, language: str = "en", metadata: Dict = None):
        self.ensure_session(session_id, patient_id, language)
        conn = self._conn()
        conn.execute(
            "INSERT INTO messages (session_id, patient_id, role, content, language, metadata) VALUES (?,?,?,?,?,?)",
            (session_id, patient_id, role, content, language, json.dumps(metadata) if metadata else None)
        )
        conn.execute("UPDATE sessions SET message_count=message_count+1, ended_at=CURRENT_TIMESTAMP WHERE session_id=?",
                     (session_id,))
        conn.commit()

    def get_conversation(self, patient_id: str, session_id: str, limit: int = 20) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT role, content, language, timestamp FROM messages WHERE patient_id=? AND session_id=? ORDER BY timestamp DESC LIMIT ?",
            (patient_id, session_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_all_conversations(self, patient_id: str, limit: int = 100) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT role, content, language, timestamp, session_id FROM messages WHERE patient_id=? ORDER BY timestamp DESC LIMIT ?",
            (patient_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ── Health Events ───────────────────────────────────────────

    def add_health_event(self, patient_id: str, event_type: str, title: str,
                         description: str = None, body_region: str = None,
                         severity: str = "mild", date: str = None, metadata: Dict = None):
        self.ensure_patient(patient_id)
        conn = self._conn()
        conn.execute(
            "INSERT INTO health_events (patient_id, event_type, title, description, body_region, severity, date, metadata) VALUES (?,?,?,?,?,?,?,?)",
            (patient_id, event_type, title, description, body_region, severity,
             date or datetime.now().strftime("%Y-%m-%d"), json.dumps(metadata) if metadata else None)
        )
        conn.commit()

    def get_health_timeline(self, patient_id: str, limit: int = 50) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM health_events WHERE patient_id=? ORDER BY date DESC, created_at DESC LIMIT ?",
            (patient_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_events_by_region(self, patient_id: str, body_region: str) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM health_events WHERE patient_id=? AND body_region=? ORDER BY date DESC",
            (patient_id, body_region)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Lab Results ─────────────────────────────────────────────

    def add_lab_result(self, patient_id: str, test_name: str, value: str,
                       unit: str = None, normal_range: str = None,
                       status: str = None, date: str = None, source: str = "manual"):
        self.ensure_patient(patient_id)
        conn = self._conn()
        conn.execute(
            "INSERT INTO lab_results (patient_id, date, test_name, value, unit, normal_range, status, source) VALUES (?,?,?,?,?,?,?,?)",
            (patient_id, date or datetime.now().strftime("%Y-%m-%d"),
             test_name, value, unit, normal_range, status, source)
        )
        conn.commit()

    def get_lab_results(self, patient_id: str, test_name: str = None, limit: int = 50) -> List[Dict]:
        conn = self._conn()
        if test_name:
            rows = conn.execute(
                "SELECT * FROM lab_results WHERE patient_id=? AND test_name=? ORDER BY date DESC LIMIT ?",
                (patient_id, test_name, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM lab_results WHERE patient_id=? ORDER BY date DESC LIMIT ?",
                (patient_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_vitals(self, patient_id: str) -> Dict:
        """Get latest value for each vital sign / lab test"""
        conn = self._conn()
        rows = conn.execute("""
            SELECT test_name, value, unit, normal_range, status, date
            FROM lab_results
            WHERE patient_id=?
            ORDER BY date DESC
        """, (patient_id,)).fetchall()

        latest = {}
        for r in rows:
            name = r["test_name"]
            if name not in latest:
                latest[name] = dict(r)
        return latest

    # ── Medical Images ──────────────────────────────────────────

    def save_medical_image(self, patient_id: str, image_path: str,
                           image_type: str = "photo", body_region: str = None,
                           description: str = None, ai_analysis: str = None,
                           session_id: str = None, date: str = None) -> int:
        self.ensure_patient(patient_id)
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO medical_images (patient_id, image_path, image_type, body_region, description, ai_analysis, session_id, date) VALUES (?,?,?,?,?,?,?,?)",
            (patient_id, image_path, image_type, body_region, description, ai_analysis,
             session_id, date or datetime.now().strftime("%Y-%m-%d"))
        )
        image_id = cur.lastrowid
        conn.commit()
        return image_id

    def delete_image(self, image_id: int, patient_id: str) -> Optional[str]:
        """Delete a medical image record. Returns the image_path for file cleanup, or None if not found."""
        conn = self._conn()
        row = conn.execute(
            "SELECT image_path FROM medical_images WHERE id=? AND patient_id=?",
            (image_id, patient_id)
        ).fetchone()
        if not row:
            return None
        image_path = row["image_path"]
        conn.execute("DELETE FROM medical_images WHERE id=? AND patient_id=?", (image_id, patient_id))
        conn.commit()
        return image_path

    def get_images(self, patient_id: str, body_region: str = None,
                   image_type: str = None) -> List[Dict]:
        conn = self._conn()
        query = "SELECT * FROM medical_images WHERE patient_id=?"
        params = [patient_id]
        if body_region:
            query += " AND body_region=?"
            params.append(body_region)
        if image_type:
            query += " AND image_type=?"
            params.append(image_type)
        query += " ORDER BY date DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_body_map(self, patient_id: str) -> Dict:
        """Get health data organized by body region"""
        conn = self._conn()

        regions = {}
        # Events by region
        rows = conn.execute(
            "SELECT body_region, COUNT(*) as count FROM health_events WHERE patient_id=? AND body_region IS NOT NULL GROUP BY body_region",
            (patient_id,)
        ).fetchall()
        for r in rows:
            regions[r["body_region"]] = {"events": r["count"], "images": 0}

        # Images by region
        rows = conn.execute(
            "SELECT body_region, COUNT(*) as count FROM medical_images WHERE patient_id=? AND body_region IS NOT NULL GROUP BY body_region",
            (patient_id,)
        ).fetchall()
        for r in rows:
            if r["body_region"] in regions:
                regions[r["body_region"]]["images"] = r["count"]
            else:
                regions[r["body_region"]] = {"events": 0, "images": r["count"]}
        return regions

    # ── Patient Summary (for LLM context) ──────────────────────

    def get_patient_context(self, patient_id: str) -> str:
        """Build patient context string for LLM prompting"""
        patient = self.get_patient(patient_id)
        if not patient:
            return ""

        parts = []
        name = patient.get("name") or patient_id
        parts.append(f"Patient: {name}")
        if patient.get("age"):
            parts.append(f"Age: {patient['age']}")
        if patient.get("gender"):
            parts.append(f"Gender: {patient['gender']}")
        if patient.get("blood_group"):
            parts.append(f"Blood Group: {patient['blood_group']}")
        if patient.get("allergies"):
            parts.append(f"Known Allergies: {patient['allergies']}")
        if patient.get("chronic_conditions"):
            parts.append(f"Chronic Conditions: {patient['chronic_conditions']}")
        if patient.get("ethnicity"):
            parts.append(f"Ethnicity/Ancestry: {patient['ethnicity']}")
        if patient.get("family_history"):
            parts.append(f"Family History: {patient['family_history']}")

        # Recent health timeline
        events = self.get_health_timeline(patient_id, limit=10)
        if events:
            parts.append("\nRecent Health History:")
            for e in events:
                parts.append(f"  [{e['date']}] {e['event_type']}: {e['title']}" +
                             (f" - {e['description']}" if e.get('description') else ""))

        # Latest vitals
        vitals = self.get_latest_vitals(patient_id)
        if vitals:
            parts.append("\nLatest Lab Results:")
            for name, v in vitals.items():
                line = f"  {name}: {v['value']}"
                if v.get("unit"):
                    line += f" {v['unit']}"
                if v.get("status"):
                    line += f" ({v['status']})"
                line += f" [{v['date']}]"
                parts.append(line)

        # Body map data
        body_map = self.get_body_map(patient_id)
        if body_map:
            parts.append("\nBody Map (regions with data):")
            for region, data in body_map.items():
                event_count = data.get("event_count", 0)
                image_count = data.get("image_count", 0)
                parts.append(f"  {region}: {event_count} events, {image_count} images")

        # Active medications
        meds = self.get_medications(patient_id, active_only=True)
        if meds:
            parts.append("\nActive Medications (currently taking):")
            for m in meds[:5]:
                line = f"  {m['name']}"
                if m.get("dosage"):
                    line += f" {m['dosage']}"
                if m.get("frequency"):
                    line += f" ({m['frequency']})"
                if m.get("start_date"):
                    line += f" [since {m['start_date']}]"
                parts.append(line)

        # Recently stopped medications
        stopped_meds = self.get_medications(patient_id, active_only=False)
        stopped = [m for m in stopped_meds if not m.get("active")]
        if stopped:
            parts.append("\nRecently Stopped Medications:")
            for m in stopped[:5]:
                line = f"  {m['name']}"
                if m.get("dosage"):
                    line += f" {m['dosage']}"
                if m.get("end_date"):
                    line += f" [stopped {m['end_date']}]"
                parts.append(line)

        return "\n".join(parts)

    def check_health(self) -> bool:
        return os.path.exists(self.db_path)

    # ── Medications ─────────────────────────────────────────────

    def add_medication(self, patient_id: str, name: str, dosage: str = None,
                       frequency: str = None, start_date: str = None, notes: str = None) -> int:
        self.ensure_patient(patient_id)
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO medications (patient_id, name, dosage, frequency, start_date, notes) VALUES (?,?,?,?,?,?)",
            (patient_id, name, dosage, frequency,
             start_date or datetime.now().strftime("%Y-%m-%d"), notes)
        )
        med_id = cur.lastrowid
        conn.commit()
        return med_id

    def get_medications(self, patient_id: str, active_only: bool = True) -> List[Dict]:
        conn = self._conn()
        q = "SELECT * FROM medications WHERE patient_id=?"
        params = [patient_id]
        if active_only:
            q += " AND active=1"
        q += " ORDER BY start_date DESC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def update_medication(self, med_id: int, patient_id: str, **kwargs) -> bool:
        conn = self._conn()
        allowed = {"name", "dosage", "frequency", "active", "end_date", "notes", "reminder_morning", "reminder_evening", "reminder_enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE medications SET {set_clause} WHERE id=? AND patient_id=?",
                     list(updates.values()) + [med_id, patient_id])
        conn.commit()
        return True

    def delete_medication(self, med_id: int, patient_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM medications WHERE id=? AND patient_id=?", (med_id, patient_id))
        conn.commit()
        return cur.rowcount > 0

    def log_medication_taken(self, med_id: int, patient_id: str, status: str = "taken") -> int:
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO medication_logs (medication_id, patient_id, status) VALUES (?,?,?)",
            (med_id, patient_id, status)
        )
        log_id = cur.lastrowid
        conn.commit()
        return log_id

    def get_medication_adherence(self, patient_id: str, med_id: int = None, days: int = 7) -> List[Dict]:
        conn = self._conn()
        if med_id:
            rows = conn.execute(
                "SELECT * FROM medication_logs WHERE patient_id=? AND medication_id=? AND taken_at >= datetime('now', ?) ORDER BY taken_at DESC",
                (patient_id, med_id, f"-{days} days")
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM medication_logs WHERE patient_id=? AND taken_at >= datetime('now', ?) ORDER BY taken_at DESC",
                (patient_id, f"-{days} days")
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_lab_result(self, result_id: int, patient_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM lab_results WHERE id=? AND patient_id=?", (result_id, patient_id))
        conn.commit()
        return cur.rowcount > 0
