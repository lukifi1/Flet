import base64

import flet as ft

from app.core.constants import LOGO_PATH, QR_ECC_LEVEL_COLORS, QR_LIMITS
from app.core.logger import get_logger
from app.core.qr_generator import generate_and_save_qr, make_qr_png_bytes
from app.core.utils import (
    get_qrcode_type,
    prepend_uri_scheme,
    qrcode_get_data_info,
    qrcode_get_ecc_level,
)

from .state import HomeState

log = get_logger(__name__)


def show_snackbar(page: ft.Page, message: str):
    """Show a snackbar notification."""
    snackbar = ft.SnackBar(ft.Text(message))
    page.overlay.append(snackbar)
    snackbar.open = True
    page.update()


# ================== LOGIC (INPUT + QR GENERATION) ==================
def handle_input_focus(e: ft.Event[ft.TextField], page: ft.Page, state: HomeState):
    text = state.input_field.value or ""
    if (text).strip() == "":
        state.input_field.hint_text = "Enter the text to encode..."
    page.update()


def handle_input_blur(e: ft.Event[ft.TextField], page: ft.Page, state: HomeState):
    if (state.input_field.value or "").strip() == "":
        state.input_field.hint_text = "Enter"
    page.update()


def handle_input_change(e: ft.Event[ft.TextField], page: ft.Page, state: HomeState):
    text = state.input_field.value or ""
    length_bytes = len(text.encode("utf-8"))

    qrcode_type = get_qrcode_type(text)
    state.badge_type.value = qrcode_type.value

    ecc_level = qrcode_get_ecc_level(text)
    state.ecc_type.value = ecc_level.value
    state.ecc_badge.bgcolor = QR_ECC_LEVEL_COLORS[ecc_level]

    state.char_info.value = str(qrcode_get_data_info(text))
    state.char_info.color = QR_ECC_LEVEL_COLORS[ecc_level]

    state.generate_button.disabled = length_bytes > QR_LIMITS.get(ecc_level, 0)
    page.update()


def gen(page: ft.Page, state: HomeState):
    text = (state.input_field.value or "").strip()
    log.debug(f"Generating QR code for input: {text[:50]}...")

    qrcode_type = get_qrcode_type(text)
    text = prepend_uri_scheme(text, qrcode_type)

    png = make_qr_png_bytes(text, logo_path=LOGO_PATH)
    state.img.src = base64.b64encode(png).decode()
    state.img.visible = True

    # Enable save button when QR is generated
    state.save_button.disabled = False
    state.save_button.bgcolor = ft.Colors.BLACK
    state.share_button.disabled = False
    state.share_button.bgcolor = ft.Colors.BLACK
    page.update()


def save_qr_code(page: ft.Page, state: HomeState):
    """Save the currently generated QR code to the database."""
    if not state.img.src:
        log.warning("No QR code generated yet")
        return

    text = (state.input_field.value or "").strip()
    if not text:
        show_snackbar(page, "Please enter text first")
        return

    try:
        qrcode_type = get_qrcode_type(text)
        text = prepend_uri_scheme(text, qrcode_type)

        category_name = state.category_dropdown.value or "General"
        is_favorite = bool(state.favorite_checkbox.data)

        # Generate and save QR code
        result = generate_and_save_qr(
            text=text,
            logo_path=LOGO_PATH,
            auto_save=True,
            metadata={"auto_generated": True},
            tags=["generated"],
            category_name=category_name,
            is_favorite=is_favorite,
        )

        if result["success"]:
            qr_id = result.get("qr_id")
            show_snackbar(page, f"QR Code saved! (ID: {qr_id})")
            log.info(f"Saved QR code {qr_id}: {text[:50]}...")
        else:
            show_snackbar(page, f"Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        log.error(f"Error saving QR code: {e}")
        show_snackbar(page, f"Error: {str(e)}")


async def do_share_qrcode(state : HomeState):
    if not state.img.src:
        return
    file = ft.ShareFile.from_bytes(
        base64.b64decode(state.img.src),
        mime_type="image/png",
        name="qrcode.png",
    )
    await state.share.share_files([file], text="Sharing a file from memory")