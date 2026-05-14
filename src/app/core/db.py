"""
SQLite Database Management Module for QR Code Generator
Handles database initialization, schema creation, and QR code persistence.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import QR_CODE_CATEGORIES
from .logger import get_logger

log = get_logger(__name__)


def _resolve_default_db_path() -> Path:
    """Resolve a writable default database path.

    Priority:
    1) Explicit path via `QRCODE_DB_PATH`
    2) Project-level `data/qrcodes.db`
    3) Module-local fallback `core/data/qrcodes.db`
    """
    env_path = os.getenv("QRCODE_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    project_root = Path(__file__).resolve().parents[3]
    project_db = project_root / "data" / "qrcodes.db"
    if project_db.parent.exists() or project_root.exists():
        return project_db

    return Path(__file__).resolve().parent / "data" / "qrcodes.db"


# Database file path
DB_PATH = _resolve_default_db_path()


class QRCodeDatabase:
    """SQLite database wrapper for QR code persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to ./data/qrcodes.db
        """
        log.info("Initializing database...")
        self.db_path = (db_path or DB_PATH).expanduser().resolve()
        log.debug(f"Database path: {self.db_path}")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure file existence is explicit; sqlite will still open/create as needed.
        if not self.db_path.exists():
            self.db_path.touch()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        log.debug(f"Opening database connection at: {self.db_path}")
        conn = sqlite3.connect(self.db_path)

        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database and create tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Enable foreign key support for this connection
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1. Categories Table
        # Stores user-defined groupings for QR codes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. QR Codes Table (Updated with category relationship)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                data TEXT NOT NULL,
                qr_type TEXT NOT NULL,
                ecc_level TEXT NOT NULL,
                binary_data BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id) 
                    ON DELETE SET NULL
            )
        """)

        cursor.execute("PRAGMA table_info(qr_codes)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "category_id" not in columns:
            cursor.execute("ALTER TABLE qr_codes ADD COLUMN category_id INTEGER")

        # 3. Favorites Table
        # A simple mapping table to flag specific QR codes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qr_code_id INTEGER NOT NULL UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (qr_code_id) REFERENCES qr_codes (id) 
                    ON DELETE CASCADE
            )
        """)

        for category_name in QR_CODE_CATEGORIES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO categories (name)
                VALUES (?)
            """,
                (category_name,),
            )

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qr_category ON qr_codes(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON qr_codes(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qr_type ON qr_codes(qr_type)")

        conn.commit()
        conn.close()

    def get_or_create_category(self, name: str) -> int:
        category_name = (name or "General").strip() or "General"
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO categories (name)
                VALUES (?)
            """,
                (category_name,),
            )
            cursor.execute(
                """
                SELECT id FROM categories WHERE name = ?
            """,
                (category_name,),
            )
            row = cursor.fetchone()
            conn.commit()

            if row is None:
                raise sqlite3.IntegrityError("Failed to retrieve category ID")

            return int(row["id"])
        finally:
            conn.close()

    def get_all_categories(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM categories
            ORDER BY name ASC
        """
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def save_qr_code(
        self,
        data: str,
        qr_type: str,
        ecc_level: str,
        binary_data: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category_name: str = "General",
        is_favorite: bool = False,
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
            category_id = self.get_or_create_category(category_name)

            cursor.execute(
                """
                INSERT INTO qr_codes 
                (category_id, data, qr_type, ecc_level, binary_data, metadata, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (
                    category_id,
                    data,
                    qr_type,
                    ecc_level,
                    binary_data,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(tags) if tags else None,
                ),
            )

            qr_id = cursor.lastrowid
            if qr_id is None:
                raise sqlite3.IntegrityError("Failed to retrieve inserted QR code ID")

            if is_favorite:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO favorites (qr_code_id)
                    VALUES (?)
                """,
                    (qr_id,),
                )

            conn.commit()
            log.info(f"QR code saved with ID: {qr_id}")
            return qr_id

        except sqlite3.IntegrityError as e:
            log.error(f"Error saving QR code: {e}")
            raise
        finally:
            conn.close()

    def set_favorite(self, qr_id: int, is_favorite: bool) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if is_favorite:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO favorites (qr_code_id)
                    VALUES (?)
                """,
                    (qr_id,),
                )
            else:
                cursor.execute(
                    """
                    DELETE FROM favorites WHERE qr_code_id = ?
                """,
                    (qr_id,),
                )

            conn.commit()
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

        cursor.execute(
            """
            SELECT 
                qr_codes.*,
                categories.name AS category_name,
                CASE WHEN favorites.id IS NULL THEN 0 ELSE 1 END AS is_favorite
            FROM qr_codes
            LEFT JOIN categories ON qr_codes.category_id = categories.id
            LEFT JOIN favorites ON qr_codes.id = favorites.qr_code_id
            WHERE qr_codes.id = ?
        """,
            (qr_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_all_qr_codes(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:

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

        cursor.execute(
            """
            SELECT 
                qr_codes.*,
                categories.name AS category_name,
                CASE WHEN favorites.id IS NULL THEN 0 ELSE 1 END AS is_favorite
            FROM qr_codes
            LEFT JOIN categories ON qr_codes.category_id = categories.id
            LEFT JOIN favorites ON qr_codes.id = favorites.qr_code_id
            ORDER BY qr_codes.created_at DESC 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary with parsed JSON fields."""
        data = dict(row)

        # Parse JSON fields
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                # Keep original value if legacy rows contain non-JSON text
                pass

        if data.get("tags"):
            try:
                data["tags"] = json.loads(data["tags"])
            except (json.JSONDecodeError, TypeError):
                # Keep original value if legacy rows contain non-JSON text
                pass

        data["is_favorite"] = bool(data.get("is_favorite"))

        return data

    def delete_all(self):
        """Delete all QR codes (for testing only)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM favorites")
        cursor.execute("DELETE FROM qr_codes")
        conn.commit()
        conn.close()
        log.info("All QR codes deleted")

    def delete_qr_code(self, qr_id: int) -> bool:
            """
            Delete a specific QR code by its ID.

            Args:
                qr_id: The ID of the QR code to delete.

            Returns:
                True if a row was deleted, False otherwise.
            """
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "DELETE FROM favorites WHERE qr_code_id = ?",
                    (qr_id,)
                )
                cursor.execute(
                    "DELETE FROM qr_codes WHERE id = ?",
                    (qr_id,)
                )
                conn.commit()

                # rowcount tells us if an actual row was removed
                deleted = cursor.rowcount > 0
                if deleted:
                    log.info(f"QR code with ID {qr_id} deleted successfully.")
                else:
                    log.warning(f"No QR code found with ID {qr_id} to delete.")

                return deleted

            except sqlite3.Error as e:
                log.error(f"Error deleting QR code {qr_id}: {e}")
                return False
            finally:
                conn.close()


# Singleton instance
_db_instance: Optional[QRCodeDatabase] = None
_db_init_error: Optional[Exception] = None


def get_db() -> QRCodeDatabase:
    """
    Get or create database instance (lazy initialization).

    Returns:
        QRCodeDatabase instance
    """
    log.debug("Accessing database instance...")
    global _db_instance, _db_init_error
    if _db_init_error is not None:
        raise RuntimeError(
            f"Database initialization previously failed: {_db_init_error}"
        )

    if _db_instance is None:
        try:
            _db_instance = QRCodeDatabase()
        except Exception as exc:
            _db_init_error = exc
            raise
    return _db_instance