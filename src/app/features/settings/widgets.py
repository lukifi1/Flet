"""Shared building blocks for the settings pages (privacy, about, imprint)."""

import flet as ft

from app.core.constants import (
    UI_ACCENT,
    UI_BORDER,
    UI_CARD_BG,
    UI_PAGE_BG,
    UI_PLACEHOLDER_BG,
    UI_PLACEHOLDER_BORDER,
    UI_PLACEHOLDER_TEXT,
    UI_TEXT_DARK,
    UI_TEXT_MUTED,
)

# Route the user came from before opening a settings page (used by the back arrow).
RETURN_ROUTE_KEY = "settings_return_route"

SETTINGS_ROUTES = {
    "privacy": "/settings/privacy",
    "about": "/settings/about",
    "imprint": "/settings/imprint",
}

_CONTENT_COLS = {"xs": 12, "sm": 10, "md": 8, "lg": 6}


def is_settings_route(route: str | None) -> bool:
    return bool(route) and route.startswith("/settings/")


def title_text(*parts: tuple[str, ft.FontWeight]) -> ft.Row:
    """Letter-spaced page title in the style of the home header ("QR GENERATOR")."""
    return ft.Row(
        [
            ft.Text(
                text,
                size=16,
                weight=weight,
                color=UI_ACCENT if i == 0 else UI_TEXT_DARK,
                style=ft.TextStyle(letter_spacing=3),
            )
            for i, (text, weight) in enumerate(parts)
        ],
        spacing=8,
        tight=True,
    )


def label(text: str) -> ft.Text:
    return ft.Text(
        text.upper(),
        size=10,
        color=UI_TEXT_MUTED,
        weight=ft.FontWeight.W_500,
        style=ft.TextStyle(letter_spacing=1.5),
    )


def paragraph(text: str) -> ft.Text:
    return ft.Text(text, size=13, color=UI_TEXT_DARK, selectable=True)


def muted(text: str) -> ft.Text:
    return ft.Text(text, size=12, color=UI_TEXT_MUTED, selectable=True)


def bullets(items: list[str]) -> ft.Column:
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("–", size=13, color=UI_TEXT_MUTED),
                    ft.Text(item, size=13, color=UI_TEXT_DARK, expand=True, selectable=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for item in items
        ],
        spacing=6,
    )


def placeholder(text: str) -> ft.Container:
    """Visible marker for legal information that must still be supplied."""
    return ft.Container(
        bgcolor=UI_PLACEHOLDER_BG,
        border=ft.Border.all(1, UI_PLACEHOLDER_BORDER),
        border_radius=2,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        content=ft.Text(
            f"[PLATZHALTER: {text}]",
            size=12,
            color=UI_PLACEHOLDER_TEXT,
            weight=ft.FontWeight.W_500,
            selectable=True,
        ),
    )


def email_link(address: str) -> ft.Text:
    return ft.Text(
        size=13,
        color=UI_TEXT_DARK,
        spans=[
            ft.TextSpan(
                address,
                url=f"mailto:{address}",
                style=ft.TextStyle(
                    color=UI_ACCENT,
                    decoration=ft.TextDecoration.UNDERLINE,
                ),
            )
        ],
    )


def web_link(text: str, url: str) -> ft.Text:
    return ft.Text(
        size=13,
        color=UI_TEXT_DARK,
        spans=[
            ft.TextSpan(
                text,
                url=url,
                style=ft.TextStyle(color=UI_ACCENT, decoration=ft.TextDecoration.UNDERLINE),
            )
        ],
    )


def name_value_rows(rows: list[tuple[str, str]]) -> ft.Column:
    """Two-column list, e.g. library name on the left and its licence on the right."""
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text(name, size=13, color=UI_TEXT_DARK, expand=True, selectable=True),
                    ft.Text(value, size=12, color=UI_TEXT_MUTED, selectable=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for name, value in rows
        ],
        spacing=6,
    )


def section(heading: str, *controls: ft.Control) -> ft.Column:
    return ft.Column(
        [label(heading), ft.Container(height=2), *controls],
        spacing=8,
    )


def divider() -> ft.Container:
    return ft.Container(height=1, bgcolor=UI_BORDER)


def notice(text: str) -> ft.Container:
    return ft.Container(
        bgcolor=UI_PLACEHOLDER_BG,
        border=ft.Border.all(1, UI_PLACEHOLDER_BORDER),
        border_radius=2,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=UI_PLACEHOLDER_TEXT),
                ft.Text(text, size=12, color=UI_PLACEHOLDER_TEXT, expand=True),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    )


def settings_page(
    page: ft.Page,
    *,
    route: str,
    title: ft.Control,
    sections: list[ft.Control],
    intro: ft.Control | None = None,
) -> ft.View:
    """Build a settings page: app bar with back arrow, white card with sections."""

    async def go_back(_e=None):
        await page.push_route(page.session.store.get(RETURN_ROUTE_KEY) or "/")

    body: list[ft.Control] = []
    for index, item in enumerate(sections):
        if index:
            body.append(ft.Container(height=4))
            body.append(divider())
            body.append(ft.Container(height=4))
        body.append(item)

    card = ft.Container(
        col=_CONTENT_COLS,
        bgcolor=UI_CARD_BG,
        border_radius=2,
        border=ft.Border.all(1, UI_BORDER),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(body, spacing=8),
    )

    rows: list[ft.Control] = []
    if intro is not None:
        rows.append(ft.ResponsiveRow([ft.Container(content=intro, col=_CONTENT_COLS)], alignment=ft.MainAxisAlignment.CENTER))
        rows.append(ft.Container(height=12))
    rows.append(ft.ResponsiveRow([card], alignment=ft.MainAxisAlignment.CENTER))
    rows.append(ft.Container(height=24))

    return ft.View(
        route=route,
        bgcolor=UI_PAGE_BG,
        padding=0,
        appbar=ft.AppBar(
            bgcolor=UI_PAGE_BG,
            elevation=0,
            toolbar_height=52,
            automatically_imply_leading=False,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=UI_TEXT_DARK,
                tooltip="Zurück",
                on_click=go_back,
            ),
            title=title,
            center_title=False,
        ),
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    content=ft.Column(rows, scroll=ft.ScrollMode.AUTO, expand=True),
                ),
                expand=True,
            )
        ],
    )
