import flet as ft

from app.features.home.view import home_view
from app.features.qr_store.view import my_codes_view

def build_view(page: ft.Page) -> ft.View:
    route = page.route

    if route == "/":
        return home_view(page)
    if route == "/my-codes":
        return my_codes_view(page)

    return ft.View(route="/404", controls=[ft.Text("Page not found")])