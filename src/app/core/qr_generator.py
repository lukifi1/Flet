import io
from typing import Optional

import qrcode
from PIL import Image, ImageDraw

from app.core.constants import (
    ECC_FUNCTION_MAP,
    LOGO_AREA_PADDING_RATIO,
    LOGO_AREA_RADIUS_RATIO,
    LOGO_AREA_RATIO,
    LOGO_MIN_ECC_LEVEL,
    QR_BACK_COLOR,
    QR_FILL_COLOR,
)
from app.core.utils import get_qrcode_type, qrcode_get_ecc_level, qrcode_select_best_ecc

from .logger import get_logger

log = get_logger(__name__)


def add_logo_inside_qr(qr_img: Image.Image, logo_path: str) -> Image.Image:
    """
    Add a logo image inside the center of the QR code image, with a dedicated room/area.
    Args:
        qr_img (Image.Image): The QR code image.
        logo_path (str): The file path to the logo image.
    """
    qr_img = qr_img.convert("RGBA")

    logo = Image.open(logo_path).convert("RGBA")

    qr_w, qr_h = qr_img.size

    # Logo area = 22% of QR size (safe)
    logo_size = int(qr_w * LOGO_AREA_RATIO)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    x = (qr_w - logo_size) // 2
    y = (qr_h - logo_size) // 2

    # 1. CUT OUT AREA IN QR (true blank space)
    mask = Image.new("RGBA", qr_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)

    padding = int(logo_size * LOGO_AREA_PADDING_RATIO)
    radius = int(logo_size * LOGO_AREA_RADIUS_RATIO)

    # Draw rounded rectangle (cut-out area)
    draw.rounded_rectangle(
        (x - padding, y - padding, x + logo_size + padding, y + logo_size + padding),
        radius=radius,
        fill=(255, 255, 255, 255),
    )

    qr_img = Image.alpha_composite(qr_img, mask)

    # 2. PASTE LOGO INTO THE CUT-OUT AREA
    qr_img.paste(logo, (x, y), logo)

    return qr_img


def make_qr_png_bytes(text: str, logo_path: str | None = None) -> bytes:
    log.debug(f"Generating QR code for text: {text[:50]}...")

    ecc = qrcode_select_best_ecc(text)

    if ecc is None:
        raise ValueError("Input text is too long to encode in a QR code.")

    qr = qrcode.QRCode(error_correction=ecc)
    qr.add_data(text or "")
    qr.make(fit=True)

    img = qr.make_image(
        fill_color=QR_FILL_COLOR,
        back_color=QR_BACK_COLOR,
    ).convert("RGB")

    # Add logo if provided and the ECC level is High
    if logo_path and ecc == ECC_FUNCTION_MAP[LOGO_MIN_ECC_LEVEL]:
        img = add_logo_inside_qr(img, logo_path)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_and_save_qr(
    text: str,
    logo_path: Optional[str] = None,
    auto_save: bool = True,
    metadata: Optional[dict] = None,
    tags: Optional[list] = None,
) -> dict:
    """
    Generate a QR code and optionally save it to the database.

    Args:
        text: Text data to encode
        logo_path: Path to logo image (optional)
        auto_save: Whether to automatically save to database
        metadata: Additional metadata for the QR code
        tags: Tags for categorization

    Returns:
        Dictionary with generation results including QR ID if saved
    """
    from app.core.db import get_db

    try:
        # Generate QR code
        png_bytes = make_qr_png_bytes(text, logo_path)

        # Get QR code properties
        qr_type = get_qrcode_type(text).value
        ecc_level = (
            qrcode_get_ecc_level(text).value if qrcode_get_ecc_level(text) else "NA"
        )

        result = {
            "success": True,
            "binary_data": png_bytes,
            "data": text,
            "qr_type": qr_type,
            "ecc_level": ecc_level,
            "qr_id": None,
        }

        # Save to database if requested
        if auto_save:
            db = get_db()
            qr_id = db.save_qr_code(
                data=text,
                qr_type=qr_type,
                ecc_level=ecc_level,
                binary_data=png_bytes,
                metadata=metadata,
                tags=tags,
            )
            result["qr_id"] = qr_id
            result["saved"] = True

        return result

    except Exception as e:
        log.error(f"Error generating/saving QR code: {e}")
        return {"success": False, "error": str(e), "binary_data": None}
