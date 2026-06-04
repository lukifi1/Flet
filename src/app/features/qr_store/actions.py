import base64
from typing import Callable, Tuple

import flet as ft

from .state import QRStoreState


def close_preview(page: ft.Page, state: QRStoreState, _e=None) -> None:
    state.preview_dialog.open = False
    page.update()


def show_qr_detail(page: ft.Page, state: QRStoreState, db, qr_code_id: int) -> None:
    detail = db.get_qr_code(qr_code_id)
    if detail and detail.get("binary_data"):
        state.preview_img.src = base64.b64encode(detail["binary_data"]).decode()
        state.preview_text.value = detail.get("data", "")
        state.preview_dialog.open = True
        page.update()


def encode_preview_src(qr_data: dict) -> str:
    if qr_data.get("binary_data"):
        return base64.b64encode(qr_data["binary_data"]).decode()
    return ""


def filter_qr_codes(
    saved_qr_codes: list[dict],
    query: str = "",
    category_filter: str = "All",
    favorites_only: bool = False,
) -> list[dict]:
    query_normalized = query.strip().lower()
    filtered_codes = []

    for qr in saved_qr_codes:
        if category_filter and category_filter != "All":
            if (qr.get("category_name") or "General") != category_filter:
                continue
        if favorites_only and not bool(qr.get("is_favorite")):
            continue

        if not query_normalized:
            filtered_codes.append(qr)
            continue

        searchable_text = (
            f"{qr.get('id', '')} {qr.get('qr_type', '')} "
            f"{qr.get('data', '')} {qr.get('created_at', '')} "
            f"{qr.get('category_name', '')}"
        ).lower()

        if query_normalized in searchable_text:
            filtered_codes.append(qr)

    return filtered_codes


def sort_qr_codes(qr_codes: list[dict], sort_by: str, ascending: bool = True) -> list[dict]:
    def sort_key(qr: dict):
        if sort_by == "created_at":
            return qr.get("created_at") or ""
        if sort_by == "category_name":
            return (qr.get("category_name") or "").lower()
        if sort_by == "id":
            return qr.get("id") or 0
        return (qr.get(sort_by) or "").lower()

    return sorted(qr_codes, key=sort_key, reverse=not ascending)


def parse_sort_value(sort_value: str) -> Tuple[str, bool]:
    parts = sort_value.split(".")
    if len(parts) == 2:
        return parts[0], parts[1] == "asc"
    return sort_value, True


def apply_search(
    state: QRStoreState,
    query: str,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    state.search_query = query
    filtered_codes = filter_qr_codes(
        state.saved_qr_codes,
        state.search_query,
        state.category_filter,
        state.favorites_only,
    )
    sorted_codes = sort_qr_codes(
        filtered_codes,
        state.sort_by,
        state.sort_ascending,
    )
    state.result_count.value = (
        f"{len(sorted_codes)} / {len(state.saved_qr_codes)} codes"
    )
    state.list_view.controls = (
        [card_builder(qr) for qr in sorted_codes]
        if sorted_codes
        else [empty_card_builder()]
    )


def handle_search_change(
    page: ft.Page,
    state: QRStoreState,
    query: str,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    apply_search(state, query, card_builder, empty_card_builder)
    page.update()


def handle_filter_change(
    page: ft.Page,
    state: QRStoreState,
    category_filter: str,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    state.category_filter = category_filter
    apply_search(state, state.search_query, card_builder, empty_card_builder)
    page.update()


def handle_favorites_filter_change(
    page: ft.Page,
    state: QRStoreState,
    favorites_only: bool,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    state.favorites_only = favorites_only
    apply_search(state, state.search_query, card_builder, empty_card_builder)
    page.update()


def handle_sort_change(
    page: ft.Page,
    state: QRStoreState,
    sort_value: str,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    state.sort_by, state.sort_ascending = parse_sort_value(sort_value)
    apply_search(state, state.search_query, card_builder, empty_card_builder)
    page.update()


def toggle_favorite(
    page: ft.Page,
    state: QRStoreState,
    db,
    qr_id: int,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    current = next((qr for qr in state.saved_qr_codes if qr.get("id") == qr_id), None)
    if current is None:
        return

    new_value = not bool(current.get("is_favorite"))
    db.set_favorite(qr_id, new_value)
    current["is_favorite"] = new_value
    apply_search(state, state.search_query, card_builder, empty_card_builder)
    page.update()


def delete_qr_code(
        page: ft.Page,
        state: QRStoreState,
        db,
        qr_id: int,
        card_builder: Callable[[dict], ft.Control],
        empty_card_builder: Callable[[], ft.Control],
) -> None:
    """Asks for confirmation, then deletes a QR code and updates the UI."""

    def close_dialog(_e=None) -> None:
        # The No button and dismiss action only close the confirmation popup.
        modal_dialog.open = False
        page.update()

    def confirm_delete(_e=None) -> None:
        try:
            # Only the Yes button reaches this point and performs the DB delete.
            modal_dialog.open = False
            db.delete_qr_code(qr_id)

            # Keep the local list in sync with the database after deleting.
            state.saved_qr_codes = [
                qr for qr in state.saved_qr_codes if qr.get("id") != qr_id
            ]

            if not state.saved_qr_codes:
                page.go("/my-codes")
            else:
                # Rebuild the visible list so search/filter/sort stay applied.
                apply_search(
                    state,
                    state.search_field.value or "",
                    card_builder,
                    empty_card_builder,
                    )
                page.update()

        except Exception as e:
            print(f"Error deleting QR code: {e}")

    # Confirmation dialog shown after the user presses the delete icon.
    modal_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Please confirm"),
        content=ft.Text(f"Are you sure you want to delete QR code: {qr_id}?"),
        actions=[
            ft.TextButton("Yes", on_click=confirm_delete),
            ft.TextButton("No", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=close_dialog,
    )

    if modal_dialog not in page.overlay:
        page.overlay.append(modal_dialog)
    modal_dialog.open = True
    page.update()