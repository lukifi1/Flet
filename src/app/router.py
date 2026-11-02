import flet as ft

from app.core.constants import UI_PAGE_BG
from app.features.home.view import home_view
from app.features.log_viewer.view import log_viewer_view
from app.features.qr_store.view import my_codes_view
from app.features.receive.view import receive_view, scan_view


def build_view(page: ft.Page) -> ft.View:
    route = page.route

    if route == "/":
        view = home_view(page)
    elif route == "/my-codes":
        view = my_codes_view(page)
    elif route == "/logs":
        view = log_viewer_view(page)
    elif route == "/receive":
        view = receive_view(page)
    elif route == "/receive/scan":
        view = scan_view(page)
    else:
        view = ft.View(route="/404", controls=[ft.Text("Page not found")])

    # Global default for all routes; individual views can still override.
    if view.bgcolor is None:
        view.bgcolor = UI_PAGE_BG

    return view
