import io

import pytest
from PIL import Image

from app.core.constants import QR_LIMITS, QRCodeEccLevel
from app.core.qr_generator import make_qr_png_bytes


# Prüft, dass die erzeugten Bytes ein vollständig lesbares PNG-Bild ergeben. (als binär in DB, als 64 in UI angezeigt)
def assert_readable_png(png_bytes: bytes):
    image = Image.open(io.BytesIO(png_bytes))
    image.load()
    assert image.format == "PNG"
    assert image.size[0] > 0
    assert image.size[1] > 0


# Prüft den maximal erlaubten Byte-Umfang für QR-Codes (Also das genau am Limit noch Akzepzeptiert wird).
def test_qr_generation_accepts_exact_maximum_byte_limit():
    text = "A" * QR_LIMITS[QRCodeEccLevel.L]

    png_bytes = make_qr_png_bytes(text)

    assert_readable_png(png_bytes)


# Prüft, dass Eingaben knapp über dem maximalen Limit abgelehnt werden.
def test_qr_generation_rejects_one_byte_over_maximum_limit():
    text = "A" * (QR_LIMITS[QRCodeEccLevel.L] + 1)

    with pytest.raises(ValueError):
        make_qr_png_bytes(text)


# Prüft die Byte-Grenze mit mehrbytefähigen Unicode-Zeichen (Also wirklich nach Byteanzahl und nicht Zeichenanzhal).
def test_qr_generation_respects_unicode_byte_limit():
    umlaut = "ä"
    text = umlaut * (QR_LIMITS[QRCodeEccLevel.L] // len(umlaut.encode("utf-8")))
    remaining_bytes = QR_LIMITS[QRCodeEccLevel.L] - len(text.encode("utf-8"))
    text += "A" * remaining_bytes

    assert len(text.encode("utf-8")) == QR_LIMITS[QRCodeEccLevel.L]
    assert_readable_png(make_qr_png_bytes(text))


# Prüft, dass Whitespace-only zwar technisch erzeugbar bleibt.
def test_qr_generation_accepts_whitespace_only_input():
    png_bytes = make_qr_png_bytes("   ")

    assert_readable_png(png_bytes)
