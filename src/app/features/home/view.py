import asyncio
import base64

import flet as ft

from app.core.constants import (
    QR_CODE_CATEGORIES,
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
from app.core.utils import qrcode_get_ecc_level

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


def home_view(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
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
        max_lines=3,
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

    category_dropdown = ft.Dropdown(
        width=190,
        value="General",
        label="Category",
        hint_text="Select category",
        options=[ft.dropdown.Option(category) for category in QR_CODE_CATEGORIES],
        bgcolor=ft.Colors.WHITE,
        color=UI_TEXT_DARK,
        border_radius=UI_INPUT_RADIUS,
        border_color=UI_INPUT_BG,
        focused_border_color=UI_BUTTON_BG,
        text_size=13,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )


    favorite_checkbox = ft.Checkbox(
        label="Favorite",
        value=False,
        label_style=ft.TextStyle(
            color=UI_TEXT_DARK,
            size=13,
            weight=ft.FontWeight.W_500,
        ),
    )

    category_and_favorite_row = ft.Row(
        [
            category_dropdown,
            ft.Container(
                width=135,
                content=favorite_checkbox,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
        width=220,
        height=220,
        fit=ft.BoxFit.CONTAIN,
        border_radius=14,
    )

    char_info = ft.Text("", size=12, color=UI_TEXT_DARK)

    generate_button = ft.Button(
        "Generate",
        height=44,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLACK,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
    )

    save_button = ft.Button(
        "Save",
        height=44,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_400,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
        disabled=True,
    )

    share = ft.Share()
    share_button = ft.Button(
        "Share",
        height=44,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLACK,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
    )

    buttons_row = ft.Row(
        [
            ft.Container(width=112, content=generate_button),
            ft.Container(width=112, content=save_button),
            ft.Container(width=112, content=share_button),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=12,
    )

    main_card = ft.Container(
        width=360,
        bgcolor=UI_CARD_BG,
        border_radius=UI_CORNER_RADIUS,
        padding=ft.Padding.symmetric(horizontal=22, vertical=18),
        content=ft.Column(
            [
                ft.Container(height=4),
                ft.Row(
                    [img],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                input_field,
                ft.Container(height=10),
                category_and_favorite_row,
                ft.Container(height=8),
                char_info,
                ft.Container(height=8),
                badges_row,
            ],
            spacing=0,
        ),
    )

    # ================== STATE INITIALIZATION ==================

    state = HomeState(
        input_field=input_field,
        badge_type=badge_type,
        ecc_type=ecc_type,
        ecc_badge=ecc_badge,
        char_info=char_info,
        generate_button=generate_button,
        img=img,
        save_button=save_button,
        share=share,
        category_dropdown=category_dropdown,
        favorite_checkbox=favorite_checkbox,
    )

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