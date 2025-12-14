import io

import numpy as np
import pytest
from PIL import Image
from qreader import QReader

from qr_generator import make_qr_png_bytes


def verify_qrcode(data) -> bool:
    png_bytes = make_qr_png_bytes(data)

    img = Image.open(io.BytesIO(png_bytes))
    img_np = np.array(img)

    qreader = QReader()
    res = qreader.detect_and_decode(img_np)

    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0
    return data in res


def test_qr_generation_returns_png_bytes():
    data = "Hello World"
    png_bytes = make_qr_png_bytes(data)

    assert isinstance(png_bytes, bytes)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_qr_generation_creates_valid_image():
    png_bytes = make_qr_png_bytes("Test QR")

    img = Image.open(io.BytesIO(png_bytes))
    assert img.size[0] > 0
    assert img.size[1] > 0


def test_empty_input_still_generates_qr():
    png = make_qr_png_bytes("")
    assert png is not None


def test_too_long_input_raises_error():
    with pytest.raises(ValueError):
        make_qr_png_bytes("A" * 10000)


def test_same_input_produces_same_png():
    data = "Deterministic QR"
    png1 = make_qr_png_bytes(data)
    png2 = make_qr_png_bytes(data)

    assert png1 == png2


def test_different_input_produces_different_png():
    png1 = make_qr_png_bytes("Hello")
    png2 = make_qr_png_bytes("World")

    assert png1 != png2


@pytest.mark.parametrize(
    "data",
    [
        "こんにちは",
        "🚀 QR test",
        "Grüße",
        "你好",
        "مرحبا",
    ],
)
def test_unicode_input_roundtrip(data):
    assert verify_qrcode(data)


@pytest.mark.parametrize(
    "data",
    [
        " ",
        "   ",
        "\n",
        " leading",
        "trailing ",
    ],
)
def test_whitespace_input(data):
    assert verify_qrcode(data)


@pytest.mark.parametrize(
    "data",
    [
        "plain text",
        "1234567890",
        "key=value&x=1",
        '{"json": true}',
    ],
)
def test_arbitrary_payloads(data):
    assert verify_qrcode(data)


def test_png_can_be_fully_loaded():
    png = make_qr_png_bytes("PNG integrity")

    img = Image.open(io.BytesIO(png))
    img.load()  # forces full decode

    assert img.format == "PNG"


def test_qr_image_mode():
    png = make_qr_png_bytes("Mode test")
    img = Image.open(io.BytesIO(png))

    assert img.mode in ("RGB", "L")


def test_larger_payload_creates_larger_qr():
    small = make_qr_png_bytes("A")
    large = make_qr_png_bytes("A" * 500)

    img_small = Image.open(io.BytesIO(small))
    img_large = Image.open(io.BytesIO(large))

    assert img_large.size[0] >= img_small.size[0]


def test_qr_generation_value():
    data = "https://example.com"
    assert verify_qrcode(data)
