import base64
from typing import Callable

import flet as ft

from .state import QRStoreState


def close_preview(page: ft.Page, state: QRStoreState, _e=None) -> None:
    state.preview_dialog.open = False
    page.update()


def show_qr_detail(page: ft.Page, state: QRStoreState, db, qr_code_id: int) -> None:
    detail = db.get_qr_code(qr_code_id)
    if detail and detail.get("binary_data"):
        state.preview_img.src = base64.b64encode(detail["binary_data"]).decode()
        state.preview_dialog.open = True
        page.update()


def encode_preview_src(qr_data: dict) -> str:
    if qr_data.get("binary_data"):
        return base64.b64encode(qr_data["binary_data"]).decode()
    return ""


def filter_qr_codes(saved_qr_codes: list[dict], query: str) -> list[dict]:
    query_normalized = query.strip().lower()
    if not query_normalized:
        return saved_qr_codes

    return [
        qr
        for qr in saved_qr_codes
        if query_normalized
        in (
            f"{qr.get('id', '')} {qr.get('qr_type', '')} "
            f"{qr.get('data', '')} {qr.get('created_at', '')}"
        ).lower()
    ]


def apply_search(
    state: QRStoreState,
    query: str,
    card_builder: Callable[[dict], ft.Control],
    empty_card_builder: Callable[[], ft.Control],
) -> None:
    filtered_codes = filter_qr_codes(state.saved_qr_codes, query)
    state.result_count.value = (
        f"{len(filtered_codes)} / {len(state.saved_qr_codes)} codes"
    )
    state.list_view.controls = (
        [card_builder(qr) for qr in filtered_codes]
        if filtered_codes
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
