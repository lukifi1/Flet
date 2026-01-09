import asyncio
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
    # ================== PAGE SETUP ==================
    page.title = "QR Maker"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # ================== HEADER / NAVIGATION ==================
    header = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "QR Code Generator",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Create scannable QR codes with live feedback",
                    size=14,
                    color=ft.Colors.GREY_700,
                ),
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(bottom=16),
    )

    # ================== STATUS BADGES ==================
    badge_type = ft.Text(QRCodeDataType.TEXT.value, color="white", size=12)
    badge = ft.Container(
        content=badge_type,
        bgcolor=ft.Colors.BLUE_600,
        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        border_radius=20,
    )

    ecc_type = ft.Text("H", color="white", size=12)
    ecc_badge = ft.Container(
        content=ecc_type,
        bgcolor=QR_ECC_LEVEL_COLORS[qrcode_get_ecc_level("")],
        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
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

    # ================== INPUT SECTION ==================
    input_field = ft.TextField(
        label="Data to encode",
        hint_text="Text, URL, email, phone number …",
        multiline=True,
        min_lines=5,
        max_lines=8,
        on_change=lambda e: handle_input_change(e),
    )

    char_info = ft.Text("", size=12)

    input_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Text("Input", weight=ft.FontWeight.BOLD),
                    input_field,
                    char_info,
                    badges_row,
                ],
                spacing=12,
            ),
        ),
    )

    # ================== RESULT SECTION ==================
    img = ft.Image(
        src=QR_NO_DATA_IMAGE,
        width=260,
        height=260,
        fit=ft.BoxFit.CONTAIN,
        border_radius=14,
    )

    generate_button = ft.Button(
        "Generate QR Code",
        icon=ft.Icons.QR_CODE_2,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: gen(),
    )

    share = ft.Share()
    share_button = ft.Button(
        "Share QR Code",
        icon=ft.Icons.SHARE,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: asyncio.create_task(do_share_qrcode()),
    )

    result_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "QR Code Preview",
                                weight=ft.FontWeight.BOLD,
                            ),
                            share_button,
                        ],
                    ),
                    ft.Text("Result", weight=ft.FontWeight.BOLD),
                    img,
                    generate_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
        ),
    )

    # ================== LOGIC ==================
    def handle_input_change(e):
        text = e.control.value or ""
        length_bytes = len(text.encode("utf-8"))

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
        img.src = base64.b64encode(png).decode()
        img.visible = True
        page.update()

    async def do_share_qrcode():
        file = ft.ShareFile.from_bytes(
            base64.b64decode(img.src),
            mime_type="image/png",
            name="qrcode.png",
        )
        result = await share.share_files(
            [file],
            text="Sharing a file from memory",
        )
        # status.value = f"Share status: {result.status}"
        # result_raw.value = f"Raw: {result.raw}"

    # ================== RESPONSIVE LAYOUT ==================
    page.add(
        ft.Column(
            [
                header,
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


# if __name__ == "__main__":
ft.run(main, assets_dir="assets")
