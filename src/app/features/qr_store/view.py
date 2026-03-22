import base64

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
from app.core.db import get_db


def my_codes_view(page: ft.Page) -> ft.View:
    db = get_db()
    try:
        # Fetch a large page so users can scroll through all saved codes in UI.
        saved_qr_codes = db.get_all_qr_codes(limit=10000)
    except Exception as exc:
        return ft.View(
            route="/my-codes",
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
                                ft.Text(
                                    f"Could not load saved QR codes: {exc}",
                                    size=13,
                                    color=UI_TEXT_DARK,
                                ),
                            ],
                            spacing=10,
                        ),
                    )
                )
            ],
        )

    preview_img = ft.Image(
        src=QR_NO_DATA_IMAGE, width=320, height=320, fit=ft.BoxFit.CONTAIN
    )

    def close_preview(e=None):
        preview_dialog.open = False
        page.update()

    preview_dialog = ft.AlertDialog(
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
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_preview),
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

    if preview_dialog not in page.overlay:
        page.overlay.append(preview_dialog)

    if not saved_qr_codes:
        return ft.View(
            route="/my-codes",
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

    def qr_item_card(qr_data: dict) -> ft.Control:
        qr_id = qr_data.get("id")
        data = qr_data.get("data", "")[:50]
        qr_type = qr_data.get("qr_type", "Text")
        created_at = qr_data.get("created_at", "")

        qr_preview_src = ""
        if qr_data.get("binary_data"):
            qr_preview_src = base64.b64encode(qr_data["binary_data"]).decode()

        def show_qr_detail(qr_code_id: int):
            detail = db.get_qr_code(qr_code_id)
            if detail and detail.get("binary_data"):
                preview_img.src = base64.b64encode(detail["binary_data"]).decode()
                preview_dialog.open = True
                page.update()

        details_controls: list[ft.Control] = [
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
                color=UI_TEXT_MUTED,
            ),
            ft.Container(height=4),
            ft.Text(
                f"Data: {data}...",
                size=12,
                color=UI_TEXT_MUTED,
            ),
            ft.Container(height=4),
            ft.Text(
                f"Date: {created_at[:10] if created_at else 'N/A'}",
                size=11,
                color=UI_TEXT_MUTED,
            ),
            ft.Container(height=10),
            ft.Button(
                "View",
                height=32,
                width=90,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=14),
                    color=UI_BUTTON_BG,
                ),
                on_click=(
                    (lambda _: show_qr_detail(qr_id))
                    if isinstance(qr_id, int)
                    else None
                ),
            ),
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

    try:
        list_view = ft.ListView(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[qr_item_card(qr) for qr in saved_qr_codes],
        )
    except Exception as exc:
        return ft.View(
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
                                ft.Text(
                                    f"Failed to render QR list: {exc}",
                                    size=13,
                                    color=UI_TEXT_DARK,
                                ),
                            ],
                            spacing=10,
                        ),
                    )
                )
            ],
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

    result_count = ft.Text(
        f"{len(saved_qr_codes)} / {len(saved_qr_codes)} codes",
        size=12,
        color=UI_TEXT_MUTED,
    )

    def apply_search(query: str) -> None:
        query_normalized = query.strip().lower()
        filtered_codes = [
            qr
            for qr in saved_qr_codes
            if query_normalized
            in (
                f"{qr.get('id', '')} {qr.get('qr_type', '')} "
                f"{qr.get('data', '')} {qr.get('created_at', '')}"
            ).lower()
        ]

        result_count.value = f"{len(filtered_codes)} / {len(saved_qr_codes)} codes"
        list_view.controls = (
            [qr_item_card(qr) for qr in filtered_codes]
            if filtered_codes
            else [build_empty_results_card()]
        )

    def on_search_change(query: str) -> None:
        apply_search(query)
        page.update()

    search_field = ft.TextField(
        hint_text="Search by ID, type, data, or date",
        prefix_icon=ft.Icons.SEARCH,
        bgcolor=UI_INPUT_BG,
        color=UI_TEXT_LIGHT,
        border_radius=14,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        hint_style=ft.TextStyle(color=UI_TEXT_LIGHT, size=12),
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        on_change=lambda e: on_search_change(e.data or ""),
    )

    apply_search("")

    return ft.View(
        route="/my-codes",
        bgcolor=UI_PAGE_BG,
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                    content=ft.Column(
                        [
                            ft.Text(
                                "My QR Codes",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=UI_TEXT_DARK,
                            ),
                            search_field,
                            result_count,
                            ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                            ft.Container(expand=True, content=list_view),
                        ],
                        expand=True,
                        spacing=10,
                    ),
                ),
                expand=True,
            )
        ],
    )
