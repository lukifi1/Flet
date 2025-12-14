import base64

import flet as ft

from constants import (
    LOGO_PATH,
    QR_ECC_LEVEL_COLORS,
    QR_LIMITS,
    QR_NO_DATA_IMAGE,
    QRCodeDataType,
)
from qr_generator import make_qr_png_bytes
from utils import (
    get_qrcode_type,
    prepend_uri_scheme,
    qrcode_get_data_info,
    qrcode_get_ecc_level,
)


def main(page: ft.Page):
    page.title = "QR Maker"
    page.scroll = "auto"
    page.padding = 20

    # ================== TITLE ==================
    title = ft.Text(
        "QR Code Generator",
        size=24,
        weight=ft.FontWeight.BOLD,
    )

    subtitle = ft.Text(
        "Generate QR codes instantly with live feedback",
        size=14,
        color=ft.Colors.GREY_700,
    )

    # ================== BADGES ==================
    badge_type = ft.Text(QRCodeDataType.TEXT.value, color="white", size=12)
    badge = ft.Container(
        content=badge_type,
        bgcolor=ft.Colors.BLUE_600,
        padding=ft.padding.symmetric(vertical=4, horizontal=10),
        border_radius=20,
    )

    ecc_type = ft.Text("H", color="white", size=12)
    ecc_badge = ft.Container(
        content=ecc_type,
        bgcolor=QR_ECC_LEVEL_COLORS[qrcode_get_ecc_level("")],
        padding=ft.padding.symmetric(vertical=4, horizontal=10),
        border_radius=20,
    )

    badges_row = ft.Row(
        [
            ft.Text("Format:", weight=ft.FontWeight.W_500),
            badge,
            ft.Text("ECC:", weight=ft.FontWeight.W_500),
            ecc_badge,
        ],
        spacing=8,
    )

    # ================== INPUT ==================
    input_field = ft.TextField(
        label="Data to encode",
        hint_text="e.g. https://example.com",
        multiline=True,
        min_lines=5,
        max_lines=8,
        on_change=lambda e: handle_input_change(e),
    )

    char_info = ft.Text("", size=12)

    input_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("QR Content", weight=ft.FontWeight.BOLD),
                    input_field,
                    char_info,
                    badges_row,
                ],
                spacing=10,
            ),
            padding=16,
        ),
        elevation=2,
    )

    # ================== QR RESULT ==================
    img = ft.Image(
        src=QR_NO_DATA_IMAGE,
        width=260,
        height=260,
        fit=ft.ImageFit.CONTAIN,
        border_radius=12,
    )

    generate_button = ft.ElevatedButton(
        "Generate QR Code",
        icon=ft.Icons.QR_CODE,
        on_click=lambda _: gen(),
        width=200,
    )

    result_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Result", weight=ft.FontWeight.BOLD),
                    img,
                    generate_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=16,
        ),
        elevation=2,
    )

    # ================== LOGIC ==================
    def handle_input_change(e):
        text = e.control.value or ""
        raw = e.control.value or ""
        length_bytes = len(raw.encode("utf-8"))

        qrcode_type = get_qrcode_type(text)
        badge_type.value = qrcode_type.value

        ecc_level = qrcode_get_ecc_level(text)
        ecc_type.value = ecc_level.value
        ecc_badge.bgcolor = QR_ECC_LEVEL_COLORS[ecc_level]

        char_info.value = qrcode_get_data_info(text)
        char_info.color = QR_ECC_LEVEL_COLORS[ecc_level]

        generate_button.disabled = length_bytes > QR_LIMITS.get(ecc_level, 0)
        page.update()

    def gen():
        text = input_field.value.strip()
        # Special case: empty input
        # if not text:
        #     img.visible = False

        qrcode_type = get_qrcode_type(text)
        # Prepend URI scheme if needed
        text = prepend_uri_scheme(text, qrcode_type)
        # Generate QR code PNG bytes
        png = make_qr_png_bytes(text, logo_path=LOGO_PATH)
        img.src_base64 = base64.b64encode(png).decode()
        img.visible = True
        page.update()

    # ================== LAYOUT ==================
    page.add(
        ft.Column(
            [
                title,
                subtitle,
                ft.Divider(height=20, color="transparent"),
                ft.ResponsiveRow(
                    [
                        ft.Column(col=12, controls=[input_card]),
                        ft.Column(col=12, controls=[result_card]),
                    ],
                    spacing=20,
                ),
            ],
            spacing=10,
        )
    )


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
