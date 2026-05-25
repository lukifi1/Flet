import pytest

from app.core.constants import QRCodeDataType
from app.core.db import QRCodeDatabase


# Erstellt für jeden Test eine isolierte temporaere SQLite-Datenbank.
@pytest.fixture
def temp_db(tmp_path):
    return QRCodeDatabase(tmp_path / "qrcodes_test.db")


# Prüft, dass eine vorhandene Kategorie wiederverwendet wird.
def test_get_or_create_category_reuses_existing_category(temp_db):
    first_id = temp_db.get_or_create_category("School")
    second_id = temp_db.get_or_create_category("School")

    assert first_id == second_id


# Prüft, dass Standard- und neue Kategorien abrufbar sind.
def test_get_all_categories_contains_default_and_custom_categories(temp_db):
    temp_db.get_or_create_category("School")

    category_names = {category["name"] for category in temp_db.get_all_categories()}

    assert "General" in category_names
    assert "Work" in category_names
    assert "School" in category_names


# Prüft, dass mehrere gespeicherte QR-Codes zurückgegeben werden.
def test_get_all_qr_codes_returns_saved_records(temp_db):
    first_id = temp_db.save_qr_code(
        data="First",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
    )
    second_id = temp_db.save_qr_code(
        data="Second",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
    )

    rows = temp_db.get_all_qr_codes()
    row_ids = {row["id"] for row in rows}

    assert first_id in row_ids
    assert second_id in row_ids
    assert len(rows) == 2


# Prüft, dass QR-Codes ohne Metadaten und Tags gespeichert werden koennen.
def test_save_qr_code_accepts_empty_metadata_and_tags(temp_db):
    qr_id = temp_db.save_qr_code(
        data="No metadata",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
        metadata=None,
        tags=None,
    )

    saved = temp_db.get_qr_code(qr_id)

    assert saved is not None
    assert saved["metadata"] is None
    assert saved["tags"] is None


# Prüft, dass beim Löschen auch der Favoriteneintrag entfernt wird.
def test_delete_qr_code_removes_favorite_entry(temp_db):
    qr_id = temp_db.save_qr_code(
        data="Favorite delete",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
        is_favorite=True,
    )

    assert temp_db.get_qr_code(qr_id)["is_favorite"] is True
    assert temp_db.delete_qr_code(qr_id) is True

    conn = temp_db._get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE qr_code_id = ?",
            (qr_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert count == 0
