import asyncio
import base64

import flet as ft

from constants import (
    LOGO_PATH,
    QR_ECC_LEVEL_COLORS,
    QR_LIMITS,
    QR_NO_DATA_IMAGE,
    QRCodeDataType,
    UI_BUTTON_RADIUS,
    UI_CARD_BG,
    UI_CORNER_RADIUS,
    UI_FONT_FAMILY,
    UI_FONT_FILE,
    UI_INPUT_BG,
    UI_INPUT_RADIUS,
    UI_TEXT_DARK,
    UI_TEXT_LIGHT,
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
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0
    page.bgcolor = ft.Colors.WHITE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.fonts = {
        UI_FONT_FAMILY: UI_FONT_FILE,
    }
    page.theme = ft.Theme(font_family=UI_FONT_FAMILY)

    title = ft.Text(
        "QR - Code Generator",
        size=22,
        weight=ft.FontWeight.W_600,
        color=UI_TEXT_DARK,
    )

    badge_type = ft.Text(QRCodeDataType.TEXT.value, color=UI_TEXT_LIGHT, size=12)
    badge = ft.Container(
        content=badge_type,
        bgcolor=ft.Colors.BLUE_600,
        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        border_radius=20,
    )

    ecc_type = ft.Text("H", color=UI_TEXT_LIGHT, size=12)
    ecc_badge = ft.Container(
        content=ecc_type,
        bgcolor=QR_ECC_LEVEL_COLORS[qrcode_get_ecc_level("")],
        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        border_radius=20,
    )

    badges_row = ft.Row(
        [
            ft.Text("Format:", weight=ft.FontWeight.W_500, color=UI_TEXT_DARK),
            badge,
            ft.Text("ECC:", weight=ft.FontWeight.W_500, color=UI_TEXT_DARK),
            ecc_badge,
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.START,
    )

    img = ft.Image(
        src=QR_NO_DATA_IMAGE,
        width=260,
        height=260,
        fit=ft.BoxFit.CONTAIN,
        border_radius=14,
    )

    input_field = ft.TextField(
        hint_text="Input",
        multiline=True,
        min_lines=2,
        max_lines=4,
        on_change=lambda e: handle_input_change(e),
        on_focus=lambda e: handle_input_focus(e),
        on_blur=lambda e: handle_input_blur(e),
        bgcolor=UI_INPUT_BG,
        color=UI_TEXT_LIGHT,
        border_radius=UI_INPUT_RADIUS,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=UI_TEXT_LIGHT,
        hint_style=ft.TextStyle(
            color=ft.Colors.with_opacity(0.65, UI_TEXT_LIGHT),
            size=12,
            weight=ft.FontWeight.W_600,
        ),
        text_size=14,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
    )

    char_info = ft.Text("", size=12, color=UI_TEXT_DARK)

    generate_button = ft.Button(
        "Generate",
        height=44,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        on_click=lambda _: gen(),
    )

    share = ft.Share()
    share_button = ft.Button(
        "Share",
        height=44,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        on_click=lambda _: asyncio.create_task(do_share_qrcode()),
    )

    buttons_row = ft.Row(
        [
            ft.Container(expand=True, content=generate_button),
            ft.Container(width=16),
            ft.Container(expand=True, content=share_button),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    main_card = ft.Container(
        width=360,
        bgcolor=UI_CARD_BG,
        border_radius=UI_CORNER_RADIUS,
        padding=ft.Padding.symmetric(horizontal=22, vertical=22),
        content=ft.Column(
            [
                ft.Text("QR-Code:", size=14, weight=ft.FontWeight.W_600, color=UI_TEXT_DARK),
                ft.Container(height=8),

                ft.Row(
                    [img],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),

                ft.Container(height=16),
                input_field,
                ft.Container(height=8),
                char_info,
                ft.Container(height=8),
                badges_row,
            ],
            spacing=0,
        ),
    )

    def handle_input_focus(e):
        if (input_field.value or "").strip() == "":
            input_field.hint_text = "Enter the text to encode..."
        page.update()

    def handle_input_blur(e):
        if (input_field.value or "").strip() == "":
            input_field.hint_text = "Enter"
        page.update()

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
        text = (input_field.value or "").strip()

        qrcode_type = get_qrcode_type(text)
        text = prepend_uri_scheme(text, qrcode_type)

        png = make_qr_png_bytes(text, logo_path=LOGO_PATH)
        img.src = base64.b64encode(png).decode()
        img.visible = True
        page.update()

    async def do_share_qrcode():
        if not img.src:
            return
        file = ft.ShareFile.from_bytes(
            base64.b64decode(img.src),
            mime_type="image/png",
            name="qrcode.png",
        )
        await share.share_files([file], text="Sharing a file from memory")

    page.add(
        ft.SafeArea(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                content=ft.Column(
                    [
                        ft.Container(height=6),
                        title,
                        ft.Container(height=16),
                        main_card,
                        ft.Container(height=18),
                        ft.Container(width=360, content=buttons_row),
                        ft.Container(height=8),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
    )


ft.run(main, assets_dir="assets")
