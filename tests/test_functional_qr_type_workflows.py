import io

import pytest
from PIL import Image

from app.core.constants import QRCodeDataType
from app.core.db import QRCodeDatabase
from app.core.qr_generator import generate_and_save_qr
from app.core.utils import prepend_uri_scheme


@pytest.fixture
def temp_db(tmp_path):
    return QRCodeDatabase(tmp_path / "qrcodes_test.db")


# Ersetzt das globale DB-Singleton durch eine isolierte temporäre Testdatenbank.
@pytest.fixture
def patched_temp_db(monkeypatch, temp_db):
    from app.core import db as db_module

    monkeypatch.setattr(db_module, "_db_instance", temp_db)
    monkeypatch.setattr(db_module, "_db_init_error", None)
    return temp_db


# Prüft, dass die QR-Erstellung ein vollständig lesbares PNG-Bild liefert.
def assert_readable_png(png_bytes: bytes):
    image = Image.open(io.BytesIO(png_bytes))
    image.load()
    assert image.format == "PNG"


# Prüft den vollständigen Workflow aus Typ-Erkennung, QR-Erstellung und DB-Speicherung.
@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("example.com", QRCodeDataType.URL.value),
        ("mailto:test@example.com", QRCodeDataType.EMAIL.value),
        ("tel:+43123456789", QRCodeDataType.PHONE.value),
        ("sms:+43123456789?body=Hallo", QRCodeDataType.SMS.value),
        ("WIFI:T:WPA;S:FH-WLAN;P:secret123;;", QRCodeDataType.WIFI.value),
        ("geo:48.2082,16.3738", QRCodeDataType.GEOLOCATION.value),
        ("Plain project note", QRCodeDataType.TEXT.value),
    ],
)
def test_generate_and_save_qr_persists_detected_qr_types(
    patched_temp_db,
    text,
    expected_type,
):
    result = generate_and_save_qr(
        text,
        auto_save=True,
        metadata={"test": "type-workflow"},
        tags=["functional"],
        category_name="Work",
        is_favorite=False,
    )

    assert result["success"] is True
    assert result["qr_type"] == expected_type
    assert_readable_png(result["binary_data"])

    saved = patched_temp_db.get_qr_code(result["qr_id"])
    assert saved is not None
    assert saved["data"] == text
    assert saved["qr_type"] == expected_type
    assert saved["category_name"] == "Work"
    assert saved["metadata"] == {"test": "type-workflow"}
    assert saved["tags"] == ["functional"]


# Prüft, dass fehlende URI-Schemata ergänzt, vorhandene Schemata aber nicht verdoppelt werden.
@pytest.mark.parametrize(
    ("text", "data_type", "expected"),
    [
        ("example.com", QRCodeDataType.URL, "https://example.com"),
        ("https://example.com", QRCodeDataType.URL, "https://example.com"),
        ("test@example.com", QRCodeDataType.EMAIL, "mailto:test@example.com"),
        ("mailto:test@example.com", QRCodeDataType.EMAIL, "mailto:test@example.com"),
        ("+43123456789", QRCodeDataType.PHONE, "tel:+43123456789"),
        ("tel:+43123456789", QRCodeDataType.PHONE, "tel:+43123456789"),
    ],
)
def test_prepend_uri_scheme_adds_missing_scheme_only_once(text, data_type, expected):
    assert prepend_uri_scheme(text, data_type) == expected
