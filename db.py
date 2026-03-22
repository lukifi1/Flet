"""
SQLite Database Management Module for QR Code Generator
Handles database initialization, schema creation, and QR code persistence.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from constants import QRCodeDataType


# Database file path
DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "qrcodes.db"


class QRCodeDatabase:
    """SQLite database wrapper for QR code persistence."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Defaults to ./data/qrcodes.db
        """
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database and create tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create QR Codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                qr_type TEXT NOT NULL,
                ecc_level TEXT NOT NULL,
                binary_data BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON qr_codes(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_qr_type ON qr_codes(qr_type)
        """)
        
        conn.commit()
        conn.close()
    
    def save_qr_code(
        self,
        data: str,
        qr_type: str,
        ecc_level: str,
        binary_data: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Save a new QR code to the database.
        
        Args:
            data: The QR code data (text content)
            qr_type: Type of QR code (from QRCodeDataType enum)
            ecc_level: Error Correction Level (L, M, Q, H)
            binary_data: PNG image bytes
            metadata: Optional metadata dictionary
            tags: Optional list of tags for categorization
        
        Returns:
            ID of the saved QR code
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO qr_codes 
                (data, qr_type, ecc_level, binary_data, metadata, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                data,
                qr_type,
                ecc_level,
                binary_data,
                json.dumps(metadata) if metadata else None,
                json.dumps(tags) if tags else None
            ))
            
            qr_id = cursor.lastrowid
            conn.commit()
            print(f"✓ QR code saved with ID: {qr_id}")
            return qr_id
            
        except sqlite3.IntegrityError as e:
            print(f"✗ Error saving QR code: {e}")
            raise
        finally:
            conn.close()
    
    def get_qr_code(self, qr_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a QR code by ID.
        
        Args:
            qr_id: ID of the QR code
        
        Returns:
            Dictionary with QR code data or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM qr_codes WHERE id = ?
        """, (qr_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_qr_codes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all QR codes with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of QR code dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM qr_codes 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
  
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary with parsed JSON fields."""
        data = dict(row)
        
        # Parse JSON fields
        if data.get("metadata"):
            data["metadata"] = json.loads(data["metadata"])
        
        if data.get("tags"):
            data["tags"] = json.loads(data["tags"])
        
        return data
    
    def delete_all(self):
        """Delete all QR codes (for testing only)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM qr_codes")
        conn.commit()
        conn.close()
        print("✓ All QR codes deleted")


# Singleton instance
_db_instance: Optional[QRCodeDatabase] = None


def get_db() -> QRCodeDatabase:
    """
    Get or create database instance (lazy initialization).
    
    Returns:
        QRCodeDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = QRCodeDatabase()
    return _db_instance
