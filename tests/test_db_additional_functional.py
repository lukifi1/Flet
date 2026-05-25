import sqlite3

import pytest

from app.core.constants import QRCodeDataType
from app.core.db import QRCodeDatabase

# Temp DB erstellen.
@pytest.fixture
def temp_db(tmp_path):
    return QRCodeDatabase(tmp_path / "qrcodes_test.db")


# Speichert einen einfachen Text-QR-Code mit Standardwerten für wiederkehrende DB-Tests.
def save_text_qr(temp_db, data: str, category_name: str = "General", is_favorite: bool = False):
    return temp_db.save_qr_code(
        data=data,
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
        category_name=category_name,
        is_favorite=is_favorite,
    )


# Prüft Pagination (Seitenweise) und Offset (übersprungene Einträge) bei gespeicherten QR-Codes.
def test_get_all_qr_codes_applies_limit_and_offset(temp_db):
    first_id = save_text_qr(temp_db, "First")
    second_id = save_text_qr(temp_db, "Second")
    third_id = save_text_qr(temp_db, "Third")

    conn = temp_db._get_connection()
    try:
        conn.execute(
            "UPDATE qr_codes SET created_at = ? WHERE id = ?",
            ("2026-01-01 10:00:00", first_id),
        )
        conn.execute(
            "UPDATE qr_codes SET created_at = ? WHERE id = ?",
            ("2026-01-02 10:00:00", second_id),
        )
        conn.execute(
            "UPDATE qr_codes SET created_at = ? WHERE id = ?",
            ("2026-01-03 10:00:00", third_id),
        )
        conn.commit()
    finally:
        conn.close()

    first_page = temp_db.get_all_qr_codes(limit=2, offset=0)
    second_page = temp_db.get_all_qr_codes(limit=2, offset=2)

    assert [row["id"] for row in first_page] == [third_id, second_id]
    assert [row["id"] for row in second_page] == [first_id]


# Prüft, dass leere Kategorien auf General zurückfallen.
@pytest.mark.parametrize("category_name", ["", "   ", None])
def test_save_qr_code_uses_general_for_empty_category(temp_db, category_name):
    qr_id = save_text_qr(temp_db, "Fallback category", category_name=category_name)

    saved = temp_db.get_qr_code(qr_id)

    assert saved["category_name"] == "General"


# Prüft, dass neue Kategorien beim Speichern automatisch angelegt werden.
def test_save_qr_code_creates_custom_category(temp_db):
    qr_id = save_text_qr(temp_db, "Custom category", category_name="School")

    saved = temp_db.get_qr_code(qr_id)
    category_names = {category["name"] for category in temp_db.get_all_categories()}

    assert saved["category_name"] == "School"
    assert "School" in category_names


# Prüft, dass delete_all QR-Codes und Favoriten entfernt.
def test_delete_all_removes_qr_codes_and_favorites(temp_db):
    save_text_qr(temp_db, "Delete all 1", is_favorite=True)
    save_text_qr(temp_db, "Delete all 2", is_favorite=False)

    temp_db.delete_all()

    assert temp_db.get_all_qr_codes() == []

    conn = temp_db._get_connection()
    try:
        favorite_count = conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    finally:
        conn.close()

    assert favorite_count == 0


# Prüft, dass kein Favorit für eine nicht existierende QR-ID angelegt wird.
def test_set_favorite_rejects_nonexistent_qr_id(temp_db):
    with pytest.raises(sqlite3.IntegrityError):
        temp_db.set_favorite(9999, True)

    conn = temp_db._get_connection()
    try:
        favorite_count = conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    finally:
        conn.close()

    assert favorite_count == 0


# Prüft, dass alte oder defekte JSON-Felder beim Lesen nicht abstürzen.
def test_get_qr_code_keeps_invalid_legacy_json_fields(temp_db):
    qr_id = save_text_qr(temp_db, "Legacy JSON")

    conn = temp_db._get_connection()
    try:
        conn.execute(
            "UPDATE qr_codes SET metadata = ?, tags = ? WHERE id = ?",
            ("not-json", "[broken", qr_id),
        )
        conn.commit()
    finally:
        conn.close()

    saved = temp_db.get_qr_code(qr_id)

    assert saved["metadata"] == "not-json"
    assert saved["tags"] == "[broken"
