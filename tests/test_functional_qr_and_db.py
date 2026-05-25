import io

import pytest
from PIL import Image

from app.core.constants import QRCodeDataType
from app.core.db import QRCodeDatabase
from app.core.qr_generator import generate_and_save_qr, make_qr_png_bytes


# Prüft, dass erzeugte Bilddaten ein gueltiges PNG enthalten.
def assert_valid_png(png_bytes: bytes) -> Image.Image:
    assert isinstance(png_bytes, bytes)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    image = Image.open(io.BytesIO(png_bytes))
    image.load()
    assert image.format == "PNG"
    assert image.size[0] > 0
    assert image.size[1] > 0
    return image


# Erstellt für jeden Test eine isolierte temporäre SQLite-Datenbank.
@pytest.fixture
def temp_db(tmp_path):
    return QRCodeDatabase(tmp_path / "qrcodes_test.db")


# Ersetzt das globale DB-Singleton durch die temporaere Testdatenbank.
@pytest.fixture
def patched_temp_db(monkeypatch, temp_db):
    from app.core import db as db_module

    monkeypatch.setattr(db_module, "_db_instance", temp_db)
    monkeypatch.setattr(db_module, "_db_init_error", None)
    return temp_db


# Prüft, dass die QR-Code-Erstellung ein lesbares PNG erzeugt.
def test_functional_qr_creation_returns_readable_png():
    png_bytes = make_qr_png_bytes("https://example.com")

    image = assert_valid_png(png_bytes)
    assert image.mode in ("RGB", "RGBA", "L")


# Prüft, dass zu lange Eingaben bei der QR-Erstellung abgelehnt werden.
def test_functional_qr_creation_rejects_text_that_is_too_long():
    with pytest.raises(ValueError):
        make_qr_png_bytes("A" * 10000)


# Prüft, dass QR-Code-Daten inklusive Metadaten gespeichert und gelesen werden.
def test_database_saves_and_reads_qr_code_with_metadata(temp_db):
    png_bytes = make_qr_png_bytes("Project QR")

    qr_id = temp_db.save_qr_code(
        data="Project QR",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
        binary_data=png_bytes,
        metadata={"source": "functional-test"},
        tags=["pytest", "database"],
        category_name="Work",
        is_favorite=True,
    )

    saved = temp_db.get_qr_code(qr_id)

    assert saved is not None
    assert saved["id"] == qr_id
    assert saved["data"] == "Project QR"
    assert saved["qr_type"] == QRCodeDataType.TEXT.value
    assert saved["ecc_level"] == "H"
    assert saved["binary_data"] == png_bytes
    assert saved["metadata"] == {"source": "functional-test"}
    assert saved["tags"] == ["pytest", "database"]
    assert saved["category_name"] == "Work"
    assert saved["is_favorite"] is True


# Prueft, dass der Favoritenstatus in der Datenbank gesetzt und entfernt wird.
def test_database_updates_favorite_status(temp_db):
    qr_id = temp_db.save_qr_code(
        data="Favorite toggle",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
        category_name="General",
        is_favorite=False,
    )

    assert temp_db.get_qr_code(qr_id)["is_favorite"] is False

    temp_db.set_favorite(qr_id, True)
    assert temp_db.get_qr_code(qr_id)["is_favorite"] is True

    temp_db.set_favorite(qr_id, False)
    assert temp_db.get_qr_code(qr_id)["is_favorite"] is False


# Prueft, dass QR-Codes aus der Datenbank gelöscht werden können.
def test_database_deletes_qr_code(temp_db):
    qr_id = temp_db.save_qr_code(
        data="Delete me",
        qr_type=QRCodeDataType.TEXT.value,
        ecc_level="H",
    )

    assert temp_db.get_qr_code(qr_id) is not None
    assert temp_db.delete_qr_code(qr_id) is True
    assert temp_db.get_qr_code(qr_id) is None
    assert temp_db.delete_qr_code(qr_id) is False


# Prüft den kompletten Workflow: QR-Code erzeugen und automatisch speichern.
def test_generate_and_save_qr_creates_png_and_persists_record(patched_temp_db):
    result = generate_and_save_qr(
        "https://example.com",
        auto_save=True,
        metadata={"created_by": "pytest"},
        tags=["functional", "qr"],
        category_name="Links",
        is_favorite=True,
    )

    assert result["success"] is True
    assert result["saved"] is True
    assert result["qr_id"] is not None
    assert result["data"] == "https://example.com"
    assert result["qr_type"] == QRCodeDataType.URL.value
    assert_valid_png(result["binary_data"])

    saved = patched_temp_db.get_qr_code(result["qr_id"])
    assert saved is not None
    assert saved["data"] == "https://example.com"
    assert saved["category_name"] == "Links"
    assert saved["metadata"] == {"created_by": "pytest"}
    assert saved["tags"] == ["functional", "qr"]
    assert saved["is_favorite"] is True


# Prüft, dass auto_save=False keinen Datenbankeintrag erzeugt.
def test_generate_and_save_qr_without_auto_save_does_not_persist(patched_temp_db):
    result = generate_and_save_qr("No autosave", auto_save=False)

    assert result["success"] is True
    assert result["qr_id"] is None
    assert "saved" not in result
    assert_valid_png(result["binary_data"])
    assert patched_temp_db.get_all_qr_codes() == []


# Prüft, dass der Workflow bei zu langem Text eine Fehlerantwort liefert.
def test_generate_and_save_qr_returns_error_for_too_long_text(patched_temp_db):
    result = generate_and_save_qr("A" * 10000, auto_save=True)

    assert result["success"] is False
    assert "too long" in result["error"]
    assert result["binary_data"] is None
    assert patched_temp_db.get_all_qr_codes() == []


# Prüft, dass der erkannte QR-Typ beim Speichern übernommen wird.
def test_generate_and_save_qr_detects_and_saves_email_type(patched_temp_db):
    result = generate_and_save_qr("mailto:test@example.com", auto_save=True)

    assert result["success"] is True
    assert result["qr_type"] == QRCodeDataType.EMAIL.value

    saved = patched_temp_db.get_qr_code(result["qr_id"])
    assert saved is not None
    assert saved["qr_type"] == QRCodeDataType.EMAIL.value
