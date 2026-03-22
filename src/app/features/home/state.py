from dataclasses import dataclass

import flet as ft


@dataclass
class HomeState:
    """State for the Home view."""

    input_field: ft.TextField
    badge_type: ft.Text
    ecc_type: ft.Text
    ecc_badge: ft.Container
    char_info: ft.Text
    generate_button: ft.Button
    img: ft.Image  # Holds the generated QR code image
    save_button: ft.Button
    share: ft.Share  # For sharing the generated QR code

    qr_code_data: str = ""

    qr_code_type: str = "Unknown"
    qr_code_ecc_level: str = "Unknown"
    qr_code_char_info: str = ""
    is_generate_disabled: bool = True
    is_save_disabled: bool = True
