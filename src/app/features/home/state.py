from dataclasses import dataclass

import flet as ft


@dataclass
class HomeState:
    """State for the Home view."""

    input_field: ft.TextField
    badge_type: ft.Text
    capacity_label: ft.Text
    capacity_bar: ft.ProgressBar
    capacity_warning: ft.Text
    generate_button: ft.Button
    img: ft.Image  # Holds the generated QR code image
    save_button: ft.Button
    share_button: ft.Button
    share: ft.Share  # For sharing the generated QR code
    category_dropdown: ft.Dropdown
    favorite_checkbox: ft.IconButton

    qr_code_data: str = ""

    qr_code_type: str = "Unknown"
    is_generate_disabled: bool = True
    is_save_disabled: bool = True