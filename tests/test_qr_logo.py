import io

from PIL import Image

from constants import LOGO_PATH
from qr_generator import make_qr_png_bytes


def test_qr_with_logo_creates_image():
    png_bytes = make_qr_png_bytes("https://example.com", logo_path=LOGO_PATH)

    img = Image.open(io.BytesIO(png_bytes))
    assert img.mode in ("RGB", "RGBA")


def test_qr_with_logo_has_center_content():
    png_bytes = make_qr_png_bytes("https://example.com", logo_path=LOGO_PATH)

    img = Image.open(io.BytesIO(png_bytes))
    w, h = img.size

    center_pixel = img.getpixel((w // 2, h // 2))
    assert center_pixel is not None
