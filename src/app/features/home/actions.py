import flet as ft

from app.core.constants import QR_ECC_LEVEL_COLORS, QR_LIMITS
from app.core.utils import get_qrcode_type, qrcode_get_data_info, qrcode_get_ecc_level

from .state import HomeState


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
