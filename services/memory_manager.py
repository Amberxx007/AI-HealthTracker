"""
Advanced Memory Manager (DEPRECATED)
──────────────────────────────────────
This module is SUPERSEDED by services/database.py (HealthDatabase).
All message storage, sessions, and patient data are now handled by HealthDatabase.
This file is kept for backward compatibility with legacy voice pipeline.
DO NOT use for new features — use HealthDatabase instead.
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
from pathlib import Path
import hashlib

from utils.utils_logger import setup_logger

logger = setup_logger(__name__)


class MemoryManager:
    """
    Enterprise conversation memory with:
    - Multi-session support
    - Full conversation history
    - Image tracking
    - Search capabilities
    - Analytics
    """
    
    def __init__(self, db_path: str = "data/conversations/medical_ai.db"):
        """Initialize memory manager"""
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Memory Manager initialized with DB: {db_path}")
    
    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                total_sessions INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                language TEXT,
                summary TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT,
                original_language TEXT,
                translation TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        # Images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT NOT NULL,
                analysis TEXT,
                interpretation TEXT,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_patient ON messages(patient_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_patient ON sessions(patient_id, started_at)")
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized")
    
    def _ensure_patient_exists(self, patient_id: str):
        """Ensure patient record exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = ?",
            (patient_id,)
        )
        
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO patients (patient_id) VALUES (?)",
                (patient_id,)
            )
            conn.commit()
        
        conn.close()
    
    def _ensure_session_exists(self, session_id: str, patient_id: str, language: str = "en"):
        """Ensure session record exists"""
        self._ensure_patient_exists(patient_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO sessions (session_id, patient_id, language)
                VALUES (?, ?, ?)
            """, (session_id, patient_id, language))
            
            # Update patient session count
            cursor.execute("""
                UPDATE patients 
                SET total_sessions = total_sessions + 1,
                    last_seen = CURRENT_TIMESTAMP
                WHERE patient_id = ?
            """, (patient_id,))
            
            conn.commit()
        
        conn.close()
    
    def save_message(
        self,
        patient_id: str,
        session_id: str,
        role: str,
        content: str,
        language: str = "en",
        metadata: Optional[Dict] = None
    ):
        """
        Save a message to conversation history
        
        Args:
            patient_id: Patient identifier
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            language: Message language
            metadata: Additional data
        """
        self._ensure_session_exists(session_id, patient_id, language)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract translation if present
        original_lang = metadata.get("original_language") if metadata else None
        translation = metadata.get("translation") if metadata else None
        
        cursor.execute("""
            INSERT INTO messages 
            (session_id, patient_id, role, content, language, original_language, translation, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            patient_id,
            role,
            content,
            language,
            original_lang,
            translation,
            json.dumps(metadata) if metadata else None
        ))
        
        # Update session message count
        cursor.execute("""
            UPDATE sessions 
            SET message_count = message_count + 1,
                ended_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
        """, (session_id,))
        
        # Update patient message count
        cursor.execute("""
            UPDATE patients 
            SET total_messages = total_messages + 1,
                last_seen = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """, (patient_id,))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Saved message for patient {patient_id} in session {session_id}")
    
    def save_image(
        self,
        patient_id: str,
        session_id: str,
        image_path: str,
        analysis: str,
        interpretation: str,
        description: Optional[str] = None
    ):
        """Save image analysis to memory"""
        self._ensure_session_exists(session_id, patient_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO images
            (session_id, patient_id, image_path, analysis, interpretation, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, patient_id, image_path, analysis, interpretation, description))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved image analysis for patient {patient_id}")
    
    def get_conversation_history(
        self,
        patient_id: str,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent conversation history for LLM context
        
        Returns:
            List of message dicts with role and content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, language, timestamp
            FROM messages
            WHERE patient_id = ? AND session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (patient_id, session_id, limit))
        
        messages = []
        for row in reversed(cursor.fetchall()):  # Reverse to get chronological
            messages.append({
                "role": row[0],
                "content": row[1],
                "language": row[2],
                "timestamp": row[3]
            })
        
        conn.close()
        
        return messages
    
    def get_full_history(
        self,
        patient_id: str,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get full conversation history with metadata
        
        Returns:
            List of detailed message dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute("""
                SELECT 
                    id, session_id, timestamp, role, content, language,
                    original_language, translation, metadata
                FROM messages
                WHERE patient_id = ? AND session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (patient_id, session_id, limit))
        else:
            cursor.execute("""
                SELECT 
                    id, session_id, timestamp, role, content, language,
                    original_language, translation, metadata
                FROM messages
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (patient_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "session_id": row[1],
                "timestamp": row[2],
                "role": row[3],
                "content": row[4],
                "language": row[5],
                "original_language": row[6],
                "translation": row[7],
                "metadata": json.loads(row[8]) if row[8] else {}
            })
        
        conn.close()
        
        return messages
    
    def get_all_sessions(self, patient_id: str) -> List[Dict]:
        """Get all sessions for a patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                session_id, started_at, ended_at, message_count, language, summary
            FROM sessions
            WHERE patient_id = ?
            ORDER BY started_at DESC
        """, (patient_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "started_at": row[1],
                "ended_at": row[2],
                "message_count": row[3],
                "language": row[4],
                "summary": row[5]
            })
        
        conn.close()
        
        return sessions
    
    def get_patient_stats(self, patient_id: str) -> Dict:
        """Get patient statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                first_seen, last_seen, total_sessions, total_messages
            FROM patients
            WHERE patient_id = ?
        """, (patient_id,))
        
        row = cursor.fetchone()
        
        if row:
            stats = {
                "patient_id": patient_id,
                "first_seen": row[0],
                "last_seen": row[1],
                "total_sessions": row[2],
                "total_messages": row[3]
            }
        else:
            stats = {
                "patient_id": patient_id,
                "exists": False
            }
        
        conn.close()
        
        return stats
    
    def search_messages(
        self,
        patient_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search through messages
        
        Args:
            patient_id: Patient identifier
            query: Search query
            limit: Max results
            
        Returns:
            List of matching messages
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, session_id, timestamp, role, content, language
            FROM messages
            WHERE patient_id = ? AND content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (patient_id, f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "session_id": row[1],
                "timestamp": row[2],
                "role": row[3],
                "content": row[4],
                "language": row[5]
            })
        
        conn.close()
        
        return results
    
    def get_session_images(self, session_id: str) -> List[Dict]:
        """Get all images from a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, timestamp, image_path, analysis, interpretation, description
            FROM images
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """, (session_id,))
        
        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "timestamp": row[1],
                "image_path": row[2],
                "analysis": row[3],
                "interpretation": row[4],
                "description": row[5]
            })
        
        conn.close()
        
        return images
    
    def check_health(self) -> bool:
        """Check if database is accessible"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to load memory patterns: {e}")
            return False


if __name__ == "__main__":
    # Test memory manager
    manager = MemoryManager()
    
    # Test saving message
    manager.save_message(
        patient_id="test_patient",
        session_id="test_session_1",
        role="user",
        content="I have a headache",
        language="en"
    )
    
    # Get history
    history = manager.get_conversation_history(
        patient_id="test_patient",
        session_id="test_session_1"
    )
    
    print(f"History: {history}")
    
    # Get stats
    stats = manager.get_patient_stats("test_patient")
    print(f"Stats: {stats}")
