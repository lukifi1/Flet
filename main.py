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
    UI_NAV_BG,
    UI_NAV_ICON_SELECTED,
    UI_NAV_ICON_UNSELECTED,
)
from qr_generator import make_qr_png_bytes, generate_and_save_qr
from utils import (
    get_qrcode_type,
    prepend_uri_scheme,
    qrcode_get_data_info,
    qrcode_get_ecc_level,
)
from db import get_db


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
        border_radius=14
    )

    # ================== INPUT SECTION ==================
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
            color=UI_TEXT_LIGHT,
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
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color=UI_CARD_BG,
        ),
        on_click=lambda _: gen(),
    )

    save_button = ft.Button(
        "Save",
        height=44,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color="#2E7D32",  # Green color for save
        ),
        on_click=lambda _: save_qr_code(),
        disabled=True,
    )

    share = ft.Share()
    share_button = ft.Button(
        "Share",
        height=44,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
            color=UI_CARD_BG,
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

    # ================== LOGIC (INPUT + QR GENERATION) ==================
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
        
        # Enable save button when QR is generated
        save_button.disabled = False
        page.update()

    def save_qr_code():
        """Save the currently generated QR code to the database."""
        if not img.src:
            print("✗ No QR code generated yet")
            return
        
        text = (input_field.value or "").strip()
        if not text:
            show_snackbar("Please enter text first")
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
                tags=["generated"]
            )
            
            if result["success"]:
                qr_id = result.get("qr_id")
                show_snackbar(f"✓ QR Code saved! (ID: {qr_id})")
                print(f"✓ Saved QR code {qr_id}: {text[:50]}...")
            else:
                show_snackbar(f"✗ Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"✗ Error saving QR code: {e}")
            show_snackbar(f"✗ Error: {str(e)}")

    def show_snackbar(message: str):
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



    # ================== MY QR CODES ==================
    DEMO_QR_SRC = "/demo-qr.png"

    preview_img = ft.Image(
        src=DEMO_QR_SRC,
        width=320,
        height=320,
        fit=ft.BoxFit.CONTAIN,
    )

    def close_preview(e=None):
        preview_dialog.open = False
        page.update()

    preview_dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#AAB3A8",
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "QR Code",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=UI_TEXT_DARK,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                on_click=close_preview,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        padding=14,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        content=ft.Row(
                            [preview_img],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ),
                ],
                spacing=0,
            ),
        ),
    )

    page.overlay.append(preview_dialog)

    # ================== ROUTING (HOME + MY CODES) ==================
    def home_view():
        return ft.SafeArea(
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

    def my_codes_view():
        """Display saved QR codes from database."""
        db = get_db()
        saved_qr_codes = db.get_all_qr_codes(limit=50)
        
        if not saved_qr_codes:
            return ft.SafeArea(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        icon_color=UI_TEXT_DARK,
                                        on_click=lambda _: page.go("/"),
                                    ),
                                    ft.Text(
                                        "My QR Codes",
                                        size=18,
                                        weight=ft.FontWeight.W_600,
                                        color=UI_TEXT_DARK,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "No QR codes saved yet",
                                            size=16,
                                            color=UI_TEXT_LIGHT,
                                            text_align=ft.TextAlign.CENTER,
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            )
                        ],
                        spacing=10,
                    ),
                )
            )
        
        def qr_item_card(qr_data: dict):
            """Create a card for displaying a saved QR code."""
            qr_id = qr_data.get("id")
            data = qr_data.get("data", "")[:50]
            qr_type = qr_data.get("qr_type", "Text")
            created_at = qr_data.get("created_at", "")
            
            # Create image from binary data if available
            qr_preview_src = ""
            if qr_data.get("binary_data"):
                qr_preview_src = base64.b64encode(qr_data["binary_data"]).decode()
            
            def show_qr_detail(qr_id):
                """Show detail view of QR code."""
                detail = db.get_qr_code(qr_id)
                if detail and detail.get("binary_data"):
                    preview_img.src = base64.b64encode(detail["binary_data"]).decode()
                    preview_dialog.open = True
                    page.update()
            
            return ft.Container(
                bgcolor=UI_CARD_BG,
                border_radius=18,
                padding=16,
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"ID: {qr_id}",
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=UI_TEXT_DARK,
                                ),
                                ft.Container(height=4),
                                ft.Text(
                                    f"Type: {qr_type}",
                                    size=12,
                                    color=UI_TEXT_LIGHT,
                                ),
                                ft.Container(height=4),
                                ft.Text(
                                    f"Data: {data}...",
                                    size=12,
                                    color=UI_TEXT_LIGHT,
                                ),
                                ft.Container(height=4),
                                ft.Text(
                                    f"Date: {created_at[:10] if created_at else 'N/A'}",
                                    size=11,
                                    color=UI_TEXT_LIGHT,
                                ),
                                ft.Container(height=10),
                                ft.Button(
                                    "View",
                                    height=32,
                                    width=90,
                                    color=ft.Colors.WHITE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=14),
                                        color=UI_CARD_BG,
                                    ),
                                    on_click=lambda _: show_qr_detail(qr_id),
                                ),
                            ],
                            spacing=0,
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            width=80,
                            height=80,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=12,
                            content=ft.Image(
                                src=qr_preview_src if qr_preview_src else QR_NO_DATA_IMAGE,
                                width=76,
                                height=76,
                                fit=ft.BoxFit.CONTAIN,
                            ) if qr_preview_src else ft.Text("N/A", size=10, color=UI_TEXT_LIGHT),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        
        list_view = ft.ListView(
            expand=True,
            spacing=12,
            padding=0,
            controls=[qr_item_card(qr) for qr in saved_qr_codes],
        )

        return ft.SafeArea(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=UI_TEXT_DARK,
                                    on_click=lambda _: page.go("/"),
                                ),
                                ft.Text(
                                    "My QR Codes",
                                    size=18,
                                    weight=ft.FontWeight.W_600,
                                    color=UI_TEXT_DARK,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                        list_view,
                    ],
                    spacing=10,
                ),
            )
        )


    # ================== ROUTING (HOME + MY CODES) ==================
    def render_route():
        page.controls.clear()

        if page.route == "/my-codes":
            page.controls.append(my_codes_view())

            home_btn.icon_color = UI_NAV_ICON_UNSELECTED
            codes_btn.icon_color = UI_NAV_ICON_SELECTED
        else:
            page.controls.append(home_view())

            home_btn.icon_color = UI_NAV_ICON_SELECTED
            codes_btn.icon_color = UI_NAV_ICON_UNSELECTED

        page.update()

    def on_route_change(e):
        render_route()

    home_btn = ft.IconButton(
        icon=ft.Icons.HOME,
        icon_color=UI_NAV_ICON_SELECTED,
        on_click=lambda _: page.go("/"),
    )

    codes_btn = ft.IconButton(
        icon=ft.Icons.QR_CODE_2,
        icon_color=UI_NAV_ICON_UNSELECTED,
        on_click=lambda _: page.go("/my-codes"),
    )

    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=UI_NAV_BG,
        content=ft.Row(
            [home_btn, codes_btn],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )

    page.on_route_change = on_route_change
    page.go(page.route or "/")


ft.run(main, assets_dir="assets")
