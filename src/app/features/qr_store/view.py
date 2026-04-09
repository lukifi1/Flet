import flet as ft

from app.core.constants import QR_NO_DATA_IMAGE, UI_PAGE_BG, UI_TEXT_DARK, UI_TEXT_MUTED
from app.core.db import get_db
from app.core.logger import get_logger

from .actions import (
    close_preview,
    encode_preview_src,
    handle_search_change,
    show_qr_detail,
)
from .state import QRStoreState
from .widgets import (
    build_empty_results_card,
    build_empty_saved_codes_view,
    build_error_view,
    build_preview_dialog,
    build_qr_item_card,
    build_search_field,
)

log = get_logger(__name__)


def my_codes_view(page: ft.Page) -> ft.View:
    ROUTE = "/my-codes"
    db = get_db()

    try:
        # Fetch a large page so users can scroll through all saved codes in UI.
        saved_qr_codes = db.get_all_qr_codes(limit=10000)
    except Exception as exc:
        log.error(f"Error fetching saved QR codes: {exc}")
        return build_error_view(ROUTE, f"Could not load saved QR codes: {exc}")

    if not saved_qr_codes:
        return build_empty_saved_codes_view(ROUTE)

    preview_img = ft.Image(
        src=QR_NO_DATA_IMAGE,
        width=320,
        height=320,
        fit=ft.BoxFit.CONTAIN,
    )

    placeholder_dialog = ft.AlertDialog(modal=True)
    list_view = ft.ListView(
        expand=True, spacing=12, scroll=ft.ScrollMode.AUTO, controls=[]
    )
    result_count = ft.Text(
        f"{len(saved_qr_codes)} / {len(saved_qr_codes)} codes",
        size=12,
        color=UI_TEXT_MUTED,
    )

    state = QRStoreState(
        saved_qr_codes=saved_qr_codes,
        preview_img=preview_img,
        preview_dialog=placeholder_dialog,
        list_view=list_view,
        result_count=result_count,
        search_field=ft.TextField(),
    )

    state.preview_dialog = build_preview_dialog(
        preview_img=state.preview_img,
        on_close=lambda e: close_preview(page, state, e),
    )

    if state.preview_dialog not in page.overlay:
        page.overlay.append(state.preview_dialog)

    def card_builder(qr_data: dict) -> ft.Control:
        qr_id = qr_data.get("id")
        qr_preview_src = encode_preview_src(qr_data)
        # New delete wrapper
        def handle_delete(_):
            from .actions import delete_qr_code
            delete_qr_code(page, state, db, qr_id)
            # Refresh the list immediately
            handle_search_change(
                page, state, state.search_field.value or "", 
                card_builder, build_empty_results_card
            )
        return build_qr_item_card(
            qr_data=qr_data,
            qr_preview_src=qr_preview_src,
            on_view_click=(
                (lambda _: show_qr_detail(page, state, db, qr_id))
                if isinstance(qr_id, int)
                else None
            ),
            on_delete_click=handle_delete,
        )

    state.search_field = build_search_field(
        on_change=lambda e: handle_search_change(
            page=page,
            state=state,
            query=e.data or "",
            card_builder=card_builder,
            empty_card_builder=build_empty_results_card,
        )
    )

    handle_search_change(
        page=page,
        state=state,
        query="",
        card_builder=card_builder,
        empty_card_builder=build_empty_results_card,
    )

    return ft.View(
        route=ROUTE,
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
                            state.search_field,
                            state.result_count,
                            ft.Divider(height=12, thickness=1, color=UI_TEXT_DARK),
                            ft.Container(expand=True, content=state.list_view),
                        ],
                        expand=True,
                        spacing=10,
                    ),
                ),
                expand=True,
            )
        ],
    )
