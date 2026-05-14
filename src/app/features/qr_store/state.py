from dataclasses import dataclass
from typing import Optional

import flet as ft


@dataclass
class QRStoreState:
    """State container for My Codes view."""

    saved_qr_codes: list[dict]
    preview_img: ft.Image
    preview_dialog: ft.AlertDialog
    list_view: ft.ListView
    result_count: ft.Text
    search_field: ft.TextField

    search_query: str = ""
    category_filter: str = "All"
    favorites_only: bool = False
    sort_by: str = "created_at"
    sort_ascending: bool = False
    filter_dropdown: Optional[ft.Dropdown] = None
    favorites_checkbox: Optional[ft.Checkbox] = None
    sort_dropdown: Optional[ft.Dropdown] = None
