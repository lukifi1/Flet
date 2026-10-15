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
    save_sequence,
    sync_input_metadata
)
from .state import HomeState
from app.core.sequence import SequencePlayer

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

    play_button = ft.Button(
        "PLAY SEQUENCE",
        height=44,
        color=UI_TEXT_LIGHT,
        bgcolor=UI_ACCENT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
    )

    stop_button = ft.Button(
        "STOP",
        height=44,
        color=UI_TEXT_MUTED,
        bgcolor=UI_INPUT_BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UI_BUTTON_RADIUS),
        ),
    )

    sequence_status = ft.Text("", size=11, color=UI_TEXT_MUTED)
    sequence = SequencePlayer(img, sequence_status)

    sequence_row = ft.Row(
        [play_button, stop_button],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )
    play_button.expand = 2
    stop_button.expand = 1

    debug_text = ft.Text(
        page.session.store.get("share_debug") or "",
        size=12,
        color=ft.Colors.RED_700,
    )

    main_card = ft.Container(
        col={"xs": 12, "sm": 8, "md": 6, "lg": 4},
        bgcolor=UI_CARD_BG,
        border_radius=2,
        border=ft.Border.all(1, UI_BORDER),
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
                            expand=True,
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

                badge_type,
                debug_text,
            ],
            spacing=0,
        ),
    )

    generate_button.expand = 2
    save_button.expand = 1
    share_button.expand = 1

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

    def on_input_change(e):
        sequence.stop()
        handle_input_change(e, page, state)

    def on_generate(e):
        sequence.stop()
        gen(page, state)

    async def on_play(e):
        text = input_field.value or ""
        if text.strip():
            save_button.disabled = False
            save_button.bgcolor = ft.Colors.BLACK
            page.update()
        await sequence.play(text)

    def on_save(e):
        if sequence.playing:
            save_sequence(page, state, sequence)
        else:
            save_qr_code(page, state)

    input_field.on_change = on_input_change
    generate_button.on_click = on_generate
    play_button.on_click = on_play
    stop_button.on_click = lambda e: sequence.stop(restore=True)
    save_button.on_click = on_save
    share_button.on_click = lambda e: asyncio.create_task(do_share_qrcode(state))
    # ================== SHARE INTENT PREFILL ==================

    page.home_state = state
    page.share_status_control = debug_text
    shared_text = getattr(page, "qr_input_text", None)

    if shared_text and input_field.value != shared_text:
        input_field.value = shared_text
        sync_input_metadata(state)
        try:
            gen(page, state)
        except Exception as exc:
            debug_text.value = f"Shared file cannot fit in a QR code: {exc}"
            log.warning("Unable to generate QR from shared data: %s", exc)

    # ================== VIEW ==================
    return ft.View(
        route="/",
        bgcolor=UI_PAGE_BG,
        padding=0,
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=16),
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("QR", size=18, weight=ft.FontWeight.W_700, color=UI_ACCENT, style=ft.TextStyle(letter_spacing=4)),
                                    ft.Text("GENERATOR", size=18, weight=ft.FontWeight.W_300, color=UI_TEXT_DARK, style=ft.TextStyle(letter_spacing=4)),
                                ],
                                spacing=8,
                            ),
                            ft.Container(height=12),
                            ft.ResponsiveRow(
                                [main_card],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=0,
                                run_spacing=0,
                            ),
                            ft.Container(height=12),
                            ft.ResponsiveRow(
                                [
                                    ft.Container(
                                        content=buttons_row,
                                        col={"xs": 12, "sm": 8, "md": 6, "lg": 4},
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=0,
                                run_spacing=0,
                            ),
                            ft.Container(height=8),
                            ft.ResponsiveRow(
                                [
                                    ft.Container(
                                        content=sequence_row,
                                        col={"xs": 12, "sm": 8, "md": 6, "lg": 4},
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=0,
                                run_spacing=0,
                            ),
                            ft.Container(height=6),
                            sequence_status,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                ),
                expand=True,
            )
        ],
    )
