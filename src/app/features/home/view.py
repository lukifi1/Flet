import asyncio
import base64

import flet as ft

from app.core.constants import (
    QR_CODE_CATEGORIES,
    QR_NO_DATA_IMAGE,
    UI_ACCENT,
    UI_BORDER,
    UI_BUTTON_RADIUS,
    UI_CARD_BG,
    UI_INPUT_BG,
    UI_PAGE_BG,
    UI_TEXT_DARK,
    UI_TEXT_MUTED,
    UI_TEXT_LIGHT,
    QRCodeDataType,
)
from app.core.logger import get_logger

from .actions import (
    do_share_qrcode,
    gen,
    handle_input_blur,
    handle_input_change,
    handle_input_focus,
    save_qr_code,
)
from .state import HomeState

log = get_logger(__name__)


def _divider():
    return ft.Container(height=1, bgcolor=UI_BORDER)


def _label(text):
    return ft.Text(text, size=10, color=UI_TEXT_MUTED, weight=ft.FontWeight.W_500, style=ft.TextStyle(letter_spacing=1.5))


def home_view(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT

    # ================== INPUT SECTION ==================
    input_field = ft.TextField(
        hint_text="ENTER TEXT TO ENCODE",
        multiline=True,
        min_lines=2,
        max_lines=3,
        bgcolor=ft.Colors.TRANSPARENT,
        color=UI_TEXT_DARK,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=UI_ACCENT,
        hint_style=ft.TextStyle(color=UI_TEXT_MUTED, size=11, letter_spacing=1.5),
        text_size=13,
        content_padding=ft.Padding.symmetric(horizontal=0, vertical=8),
    )

    category_dropdown = ft.Dropdown(
        width=180,
        value="General",
        options=[ft.dropdown.Option(c) for c in QR_CODE_CATEGORIES],
        bgcolor=UI_INPUT_BG,
        color=UI_TEXT_DARK,
        border_radius=2,
        border_color=UI_BORDER,
        focused_border_color=UI_ACCENT,
        text_size=12,
        content_padding=ft.Padding.symmetric(horizontal=10, vertical=8),
    )

    favorite_checkbox = ft.IconButton(
        icon=ft.Icons.FAVORITE_BORDER,
        icon_color=UI_TEXT_MUTED,
        icon_size=18,
        tooltip="Favorite",
    )

    badge_type = ft.Text(QRCodeDataType.TEXT.value.upper(), color=UI_ACCENT, size=10, style=ft.TextStyle(letter_spacing=1.5))

    img = ft.Image(
        src=QR_NO_DATA_IMAGE,
        width=200,
        height=200,
        fit=ft.BoxFit.CONTAIN,
        border_radius=2,
    )

    generate_button = ft.Button(
        "GENERATE",
        height=44,
        color=UI_TEXT_LIGHT,
        bgcolor=UI_ACCENT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
    )

    save_button = ft.Button(
        "SAVE",
        height=44,
        color=UI_TEXT_MUTED,
        bgcolor=UI_INPUT_BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        disabled=True,
    )

    share = ft.Share()
    share_button = ft.Button(
        "SHARE",
        height=44,
        color=UI_TEXT_MUTED,
        bgcolor=UI_INPUT_BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        disabled=True,
    )

    main_card = ft.Container(
        width=360,
        bgcolor=UI_CARD_BG,
        border_radius=2,
        border=ft.border.all(1, UI_BORDER),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            [
                # QR image
                ft.Row([img], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                _divider(),
                ft.Container(height=16),

                # Input
                _label("INPUT"),
                ft.Container(height=6),
                input_field,
                _divider(),
                ft.Container(height=14),

                # Category + Favorite
                ft.Row(
                    [
                        ft.Column(
                            [
                                _label("CATEGORY"),
                                ft.Container(height=4),
                                category_dropdown,
                            ],
                            spacing=0,
                        ),
                        ft.Column(
                            [
                                _label("FAVORITE"),
                                favorite_checkbox,
                            ],
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=16),
                _divider(),
                ft.Container(height=14),

                # Format
                ft.Row(
                    [
                        ft.Column(
                            [
                                _label("FORMAT"),
                                ft.Container(height=4),
                                badge_type,
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=0,
        ),
    )

    generate_button.width = 150
    save_button.width = 96
    share_button.width = 96

    buttons_row = ft.Row(
        [generate_button, save_button, share_button],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )

    # ================== STATE INITIALIZATION ==================

    state = HomeState(
        input_field=input_field,
        badge_type=badge_type,
        generate_button=generate_button,
        img=img,
        save_button=save_button,
        share_button=share_button,
        share=share,
        category_dropdown=category_dropdown,
        favorite_checkbox=favorite_checkbox,
    )

    def toggle_favorite(e):
        if favorite_checkbox.icon == ft.Icons.FAVORITE_BORDER:
            favorite_checkbox.icon = ft.Icons.FAVORITE
            favorite_checkbox.icon_color = ft.Colors.RED_400
            favorite_checkbox.data = True
        else:
            favorite_checkbox.icon = ft.Icons.FAVORITE_BORDER
            favorite_checkbox.icon_color = UI_TEXT_MUTED
            favorite_checkbox.data = False
        page.update()

    favorite_checkbox.data = False
    favorite_checkbox.on_click = toggle_favorite

    # ================== EVENT HANDLERS ==================

    input_field.on_focus = lambda e: handle_input_focus(e, page, state)
    input_field.on_blur = lambda e: handle_input_blur(e, page, state)
    input_field.on_change = lambda e: handle_input_change(e, page, state)

    generate_button.on_click = lambda e: gen(page, state)
    save_button.on_click = lambda e: save_qr_code(page, state)
    share_button.on_click = lambda e: asyncio.create_task(do_share_qrcode(state))

    # ================== VIEW ==================
    return ft.View(
        route="/",
        bgcolor=UI_PAGE_BG,
        controls=[
            ft.SafeArea(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=24),
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("QR", size=18, weight=ft.FontWeight.W_700, color=UI_ACCENT, style=ft.TextStyle(letter_spacing=4)),
                                    ft.Text("GENERATOR", size=18, weight=ft.FontWeight.W_300, color=UI_TEXT_DARK, style=ft.TextStyle(letter_spacing=4)),
                                ],
                                spacing=8,
                            ),
                            ft.Container(height=20),
                            main_card,
                            ft.Container(height=12),
                            ft.Container(width=360, content=buttons_row),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        ],
    )