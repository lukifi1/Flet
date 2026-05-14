import flet as ft

from app.core.constants import (
    QR_NO_DATA_IMAGE,
    UI_BUTTON_BG,
    UI_CARD_BG,
    UI_INPUT_BG,
    UI_PAGE_BG,
    UI_TEXT_DARK,
    UI_TEXT_LIGHT,
    UI_TEXT_MUTED,
)


def build_error_view(route: str, message: str) -> ft.View:
    return ft.View(
        route=route,
        controls=[
            ft.SafeArea(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                    content=ft.Column(
                        [
                            ft.Text(
                                "My QR Codes",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=UI_TEXT_DARK,
                            ),
                            ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                            ft.Text(message, size=13, color=UI_TEXT_DARK),
                        ],
                        spacing=10,
                    ),
                )
            )
        ],
    )


def build_empty_saved_codes_view(route: str) -> ft.View:
    return ft.View(
        route=route,
        bgcolor=UI_PAGE_BG,
        controls=[
            ft.SafeArea(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                    content=ft.Column(
                        [
                            ft.Text(
                                "My QR Codes",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=UI_TEXT_DARK,
                            ),
                            ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "No QR codes saved yet",
                                            size=16,
                                            color=UI_TEXT_MUTED,
                                            text_align=ft.TextAlign.CENTER,
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                        ],
                        spacing=10,
                    ),
                )
            )
        ],
    )


def build_preview_dialog(preview_img: ft.Image, on_close) -> ft.AlertDialog:
    return ft.AlertDialog(
        modal=True,
        bgcolor=UI_CARD_BG,
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
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=on_close),
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


def build_qr_item_card(qr_data: dict, qr_preview_src: str, on_view_click, on_delete_click) -> ft.Control:
    qr_id = qr_data.get("id")
    data = qr_data.get("data", "")[:50]
    qr_type = qr_data.get("qr_type", "Text")
    created_at = qr_data.get("created_at", "")
    category_name = qr_data.get("category_name") or "General"
    is_favorite = bool(qr_data.get("is_favorite"))

    details_controls: list[ft.Control] = [
        ft.Text(f"ID: {qr_id}", size=14, weight=ft.FontWeight.W_600, color=UI_TEXT_DARK),
        ft.Container(height=4),
        ft.Text(f"Type: {qr_type}", size=12, color=UI_TEXT_MUTED),
        ft.Container(height=4),
        ft.Text(f"Category: {category_name}", size=12, color=UI_TEXT_MUTED),
        ft.Container(height=4),
        ft.Text(f"Favorite: {'Yes' if is_favorite else 'No'}", size=12, color=UI_TEXT_MUTED),
        ft.Container(height=4),
        ft.Text(f"Data: {data}...", size=12, color=UI_TEXT_MUTED),
        ft.Container(height=4),
        ft.Text(f"Date: {created_at[:10] if created_at else 'N/A'}", size=11, color=UI_TEXT_MUTED),
        ft.Container(height=10),
        ft.Row([
            ft.ElevatedButton(
                "View",
                height=32,
                width=90,
                color=ft.Colors.WHITE,
                bgcolor=UI_BUTTON_BG,
                on_click=on_view_click,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                tooltip="Delete QR",
                on_click=on_delete_click,
            ),
        ], spacing=10)
    ]

    row_controls: list[ft.Control] = [
        ft.Column(details_controls, spacing=0),
        ft.Container(expand=True),
        ft.Container(
            width=80,
            height=80,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            content=(
                ft.Image(
                    src=qr_preview_src if qr_preview_src else QR_NO_DATA_IMAGE,
                    width=76,
                    height=76,
                    fit=ft.BoxFit.CONTAIN,
                )
                if qr_preview_src
                else ft.Text("N/A", size=10, color=UI_TEXT_MUTED)
            ),
        ),
    ]

    return ft.Container(
        bgcolor=UI_CARD_BG,
        border_radius=18,
        padding=16,
        content=ft.Row(
            row_controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def build_empty_results_card() -> ft.Control:
    return ft.Container(
        bgcolor=UI_CARD_BG,
        border_radius=18,
        padding=20,
        content=ft.Text(
            "No QR codes match your search.",
            size=14,
            color=UI_TEXT_MUTED,
            text_align=ft.TextAlign.CENTER,
        ),
    )


def build_search_field(on_change) -> ft.TextField:
    return ft.TextField(
        hint_text="Search by ID, type, data, or date",
        prefix_icon=ft.Icons.SEARCH,
        bgcolor=UI_INPUT_BG,
        color=UI_TEXT_LIGHT,
        border_radius=14,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        hint_style=ft.TextStyle(color=UI_TEXT_LIGHT, size=12),
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        on_change=on_change,
    )