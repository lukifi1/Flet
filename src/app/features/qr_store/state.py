from dataclasses import dataclass

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
