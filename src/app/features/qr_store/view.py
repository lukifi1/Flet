import flet as ft

from app.core.constants import QR_CODE_CATEGORIES, QR_NO_DATA_IMAGE, UI_PAGE_BG, UI_TEXT_DARK, UI_TEXT_MUTED
from app.core.db import get_db
from app.core.logger import get_logger

from .actions import (
    close_preview,
    encode_preview_src,
    handle_filter_change,
    handle_favorites_filter_change,
    handle_search_change,
    handle_sort_change,
    show_qr_detail,
    toggle_favorite,
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

    preview_text = ft.Text(
        "",
        selectable=True,
        size=12,
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

    filter_dropdown = ft.Dropdown(
        width=170,
        value="All",
        label="Category",
        options=[ft.dropdown.Option(key="All", text="All")] + [
            ft.dropdown.Option(key=category, text=category)
            for category in QR_CODE_CATEGORIES
        ],
        bgcolor=ft.Colors.WHITE,
        color=UI_TEXT_DARK,
        border_radius=14,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.BLACK,
        text_size=12,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )

    favorites_checkbox = ft.Checkbox(
        label="Favorites only",
        value=False,
        label_style=ft.TextStyle(color=UI_TEXT_DARK, size=12),
    )

    sort_dropdown = ft.Dropdown(
        width=220,
        value="created_at.desc",
        label="Sort by",
        options=[
            ft.dropdown.Option(key="created_at.desc", text="Date: newest first"),
            ft.dropdown.Option(key="created_at.asc", text="Date: oldest first"),
            ft.dropdown.Option(key="data.asc", text="Data: A → Z"),
            ft.dropdown.Option(key="data.desc", text="Data: Z → A"),
            ft.dropdown.Option(key="id.asc", text="ID: ascending"),
            ft.dropdown.Option(key="id.desc", text="ID: descending"),
        ],
        bgcolor=ft.Colors.WHITE,
        color=UI_TEXT_DARK,
        border_radius=14,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.BLACK,
        text_size=12,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )

    state = QRStoreState(
        saved_qr_codes=saved_qr_codes,
        preview_img=preview_img,
        preview_text=preview_text,
        preview_dialog=placeholder_dialog,
        list_view=list_view,
        result_count=result_count,
        search_field=ft.TextField(),
        filter_dropdown=filter_dropdown,
        favorites_checkbox=favorites_checkbox,
        sort_dropdown=sort_dropdown,
    )

    state.preview_dialog = build_preview_dialog(
        preview_img=state.preview_img,
        preview_text=state.preview_text,
        on_close=lambda e: close_preview(page, state, e),
    )

    if state.preview_dialog not in page.overlay:
        page.overlay.append(state.preview_dialog)

    def card_builder(qr_data: dict) -> ft.Control:
        qr_id = qr_data.get("id")
        qr_preview_src = encode_preview_src(qr_data)

        def handle_delete(_):
            from .actions import delete_qr_code
            delete_qr_code(
                page=page,
                state=state,
                db=db,
                qr_id=qr_id,
                card_builder=card_builder,
                empty_card_builder=build_empty_results_card,
            )

        def handle_favorite_toggle(_):
            toggle_favorite(
                page=page,
                state=state,
                db=db,
                qr_id=qr_id,
                card_builder=card_builder,
                empty_card_builder=build_empty_results_card,
            )

        return build_qr_item_card(
            qr_data=qr_data,
            qr_preview_src=qr_preview_src,
            on_view_click=(
                (lambda _: show_qr_detail(page, state, db, qr_id))
                if isinstance(qr_id, int)
                else None
            ),
            on_favorite_click=handle_favorite_toggle,
            on_delete_click=handle_delete,
        )

    filter_dropdown.on_select = lambda e: handle_filter_change(
        page=page,
        state=state,
        category_filter=(e.data or "All") if e.data is not None else "All",
        card_builder=card_builder,
        empty_card_builder=build_empty_results_card,
    )

    favorites_checkbox.on_change = lambda e: handle_favorites_filter_change(
        page=page,
        state=state,
        favorites_only=bool(e.control.value),
        card_builder=card_builder,
        empty_card_builder=build_empty_results_card,
    )

    sort_dropdown.on_select = lambda e: handle_sort_change(
        page=page,
        state=state,
        sort_value=(e.data or "created_at.desc") if e.data is not None else "created_at.desc",
        card_builder=card_builder,
        empty_card_builder=build_empty_results_card,
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
                            ft.Row(
                                [filter_dropdown, favorites_checkbox, sort_dropdown],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                spacing=12,
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
