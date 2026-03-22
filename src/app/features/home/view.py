import asyncio
import base64

import flet as ft

from app.core.constants import (
    LOGO_PATH,
    QR_ECC_LEVEL_COLORS,
    QR_NO_DATA_IMAGE,
    UI_BUTTON_BG,
    UI_BUTTON_RADIUS,
    UI_CARD_BG,
    UI_CORNER_RADIUS,
    UI_INPUT_BG,
    UI_INPUT_RADIUS,
    UI_PAGE_BG,
    UI_SUCCESS_BG,
    UI_TEXT_DARK,
    UI_TEXT_LIGHT,
    QRCodeDataType,
)
from app.core.logger import get_logger
from app.core.qr_generator import generate_and_save_qr, make_qr_png_bytes
from app.core.utils import get_qrcode_type, prepend_uri_scheme, qrcode_get_ecc_level

from .actions import handle_input_blur, handle_input_change, handle_input_focus
from .state import HomeState

log = get_logger(__name__)


def home_view(page: ft.Page):
    title = ft.Text(
        "QR - Code Generator",
        size=22,
        weight=ft.FontWeight.W_600,
        color=UI_TEXT_DARK,
    )
    # ================== INPUT SECTION ==================
    input_field = ft.TextField(
        hint_text="Input",
        multiline=True,
        min_lines=2,
        max_lines=4,
        bgcolor=UI_INPUT_BG,
        color=UI_TEXT_LIGHT,
        border_radius=UI_INPUT_RADIUS,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=UI_TEXT_LIGHT,
        hint_style=ft.TextStyle(
            color=UI_TEXT_LIGHT,
            size=12,
            weight=ft.FontWeight.W_600,
        ),
        text_size=14,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
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

    char_info = ft.Text("", size=12, color=UI_TEXT_DARK)

    def gen(page: ft.Page):
        text = (input_field.value or "").strip()
        log.debug(f"Generating QR code for input: {text[:50]}...")

        qrcode_type = get_qrcode_type(text)
        text = prepend_uri_scheme(text, qrcode_type)

        png = make_qr_png_bytes(text, logo_path=LOGO_PATH)
        img.src = base64.b64encode(png).decode()
        img.visible = True

        # Enable save button when QR is generated
        save_button.disabled = False
        page.update()

    def save_qr_code(page: ft.Page):
        """Save the currently generated QR code to the database."""
        if not img.src:
            log.warning("No QR code generated yet")
            return

        text = (input_field.value or "").strip()
        if not text:
            show_snackbar(page, "Please enter text first")
            return

        try:
            qrcode_type = get_qrcode_type(text)
            text = prepend_uri_scheme(text, qrcode_type)

            # Generate and save QR code
            result = generate_and_save_qr(
                text=text,
                logo_path=LOGO_PATH,
                auto_save=True,
                metadata={"auto_generated": True},
                tags=["generated"],
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

    generate_button = ft.Button(
        "Generate",
        height=44,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color=UI_BUTTON_BG,
        ),
        on_click=lambda _: gen(page),
    )

    save_button = ft.Button(
        "Save",
        height=44,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color=UI_SUCCESS_BG,
        ),
        on_click=lambda e: save_qr_code(page),
        disabled=True,
    )

    share = ft.Share()
    share_button = ft.Button(
        "Share",
        height=44,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color=UI_BUTTON_BG,
        ),
        on_click=lambda _: asyncio.create_task(do_share_qrcode()),
    )
    buttons_row = ft.Row(
        [
            ft.Container(expand=True, content=generate_button),
            ft.Container(expand=True, content=save_button),
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

    state = HomeState(
        input_field=input_field,
        badge_type=badge_type,
        ecc_type=ecc_type,
        ecc_badge=ecc_badge,
        char_info=char_info,
        generate_button=generate_button,
    )

    input_field.on_focus = lambda e: handle_input_focus(e, page, state)
    input_field.on_blur = lambda e: handle_input_blur(e, page, state)
    input_field.on_change = lambda e: handle_input_change(e, page, state)

    def show_snackbar(page: ft.Page, message: str):
        """Show a snackbar notification."""
        snackbar = ft.SnackBar(ft.Text(message))
        page.overlay.append(snackbar)
        snackbar.open = True
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

    return ft.View(
        route="/",
        bgcolor=UI_PAGE_BG,
        controls=[
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
        ],
    )
