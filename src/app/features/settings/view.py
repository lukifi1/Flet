"""Settings menu (gear icon) and its three pages: privacy, about, imprint."""

import flet as ft

from app.core.constants import (
    APP_CONTACT_EMAIL,
    APP_NAME,
    APP_PUBLISHER_NAME,
    APP_VERSION,
    UI_PAGE_BG,
    UI_TEXT_DARK,
)

from .widgets import (
    RETURN_ROUTE_KEY,
    SETTINGS_ROUTES,
    email_link,
    is_settings_route,
    muted,
    name_value_rows,
    paragraph,
    section,
    settings_page,
    title_text,
    web_link,
)

DEVELOPER_TEAM = [
    "Lukas Fink",
    "Elsherif Ibrahim",
    "Noman Hadi",
    "Stangelberger Simon",
    "Emre Kilic",
]

# Read from the installed package metadata / font file (Flet 1.0.5, qrcode 8.2, Pillow 13.0,
# opencv-python 5.0, NumPy, certifi). Re-check when dependencies change.
OPEN_SOURCE_LICENSES = [
    ("Flet, flet-camera, flet-permission-handler", "Apache-2.0"),
    ("Flutter", "BSD-3-Clause"),
    ("qrcode", "BSD"),
    ("Pillow", "MIT-CMU"),
    ("OpenCV (opencv-python)", "Apache-2.0"),
    ("NumPy", "BSD-3-Clause"),
    ("certifi", "MPL-2.0"),
    ("Inter (Schrift), © The Inter Project Authors", "SIL OFL 1.1"),
]


# ================== APP BAR WITH GEAR MENU ==================


def settings_menu_button(page: ft.Page) -> ft.PopupMenuButton:
    """Small gear icon that opens the three settings entries."""

    def open_page(key: str):
        async def handler(_e=None):
            if not is_settings_route(page.route):
                page.session.store.set(RETURN_ROUTE_KEY, page.route or "/")
            await page.push_route(SETTINGS_ROUTES[key])

        return handler

    return ft.PopupMenuButton(
        icon=ft.Icons.SETTINGS_OUTLINED,
        icon_size=20,
        icon_color=UI_TEXT_DARK,
        tooltip="Einstellungen",
        bgcolor=ft.Colors.WHITE,
        items=[
            ft.PopupMenuItem(
                content="Datenschutzerklärung",
                icon=ft.Icons.PRIVACY_TIP_OUTLINED,
                on_click=open_page("privacy"),
            ),
            ft.PopupMenuItem(
                content="Über die App",
                icon=ft.Icons.INFO_OUTLINE,
                on_click=open_page("about"),
            ),
            ft.PopupMenuItem(
                content="Impressum",
                icon=ft.Icons.GAVEL_OUTLINED,
                on_click=open_page("imprint"),
            ),
        ],
    )


def main_appbar(page: ft.Page) -> ft.AppBar:
    """Slim app bar for the main tabs; only holds the gear in the top right."""
    return ft.AppBar(
        bgcolor=UI_PAGE_BG,
        elevation=0,
        toolbar_height=44,
        automatically_imply_leading=False,
        actions=[settings_menu_button(page), ft.Container(width=8)],
    )


# ================== PRIVACY ==================


def privacy_view(page: ft.Page) -> ft.View:
    return settings_page(
        page,
        route=SETTINGS_ROUTES["privacy"],
        title=title_text(("DATEN", ft.FontWeight.W_700), ("SCHUTZ", ft.FontWeight.W_300)),
        sections=[
            section(
                "Grundsatz",
                paragraph(
                    f"{APP_NAME} hat kein Benutzerkonto, keine Werbung und keine Nutzungsanalyse. "
                    "Es werden keine Daten an Server oder Dritte übertragen. "
                    "Daten werden ausschließlich lokal auf deinem Gerät und nur zur Funktion der App verarbeitet."
                ),
            ),
            section(
                "Gespeicherte Daten",
                paragraph(
                    "Nur wenn du „SAVE“ oder „Sequenz speichern“ wählst, speichert die App den QR-Code "
                    "(Inhalt, Typ, Bild, Kategorie, Favorit, Zeitstempel) lokal auf deinem Gerät. "
                ),
            ),
            section(
                "Kamera",
                paragraph(
                    "Die Kamera wird nur im Bereich „Empfangen“ zum Scannen von QR-Codes verwendet. "
                    "Dafür fragt die App deine Erlaubnis an, die du jederzeit in den Geräteeinstellungen "
                    "widerrufen kannst. Die Bilder werden nur auf dem Gerät ausgewertet, nicht gespeichert "
                    "und nicht übertragen. Es wird kein Ton aufgenommen."
                ),
            ),
            section(
                "QR-Code-Übertragung",
                paragraph(
                    "Dateien werden als Folge von QR-Codes angezeigt und vom anderen Gerät mit der Kamera "
                    "gescannt, nicht über das Netzwerk. "
                    "Eine empfangene Datei wird erst gespeichert, wenn du „Datei speichern“ wählst. "
                    "Bei „SHARE“ und „In anderer App öffnen“ gelangen die Daten an die App, die du auswählst; "
                    "dort gilt deren Datenschutzerklärung."
                ),
            ),
            section(
                "Löschung",
                paragraph(
                    "Gespeicherte QR-Codes löschst du im Tab „My Codes“ einzeln über das Papierkorb-Symbol. "
                    "Alle übrigen Daten entfernst du durch Löschen der App-Daten oder Deinstallation der App."
                ),
            ),
            section(
                "Kontakt und deine Rechte",
                paragraph(
                    "Du hast nach der DSGVO das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung "
                    "der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie auf Beschwerde bei der "
                    "zuständigen Aufsichtsbehörde. In Österreich ist das die Datenschutzbehörde:"
                ),
                web_link("dsb.gv.at", "https://www.dsb.gv.at"),
                paragraph("Bei Fragen erreichst du uns hier:"),
                email_link(APP_CONTACT_EMAIL),
            ),
            section(
                "Verantwortlicher",
                paragraph(APP_PUBLISHER_NAME),
            ),
        ],
    )


# ================== ABOUT ==================


def about_view(page: ft.Page) -> ft.View:
    return settings_page(
        page,
        route=SETTINGS_ROUTES["about"],
        title=title_text(("ÜBER", ft.FontWeight.W_700), ("DIE APP", ft.FontWeight.W_300)),
        sections=[
            section(
                APP_NAME,
                paragraph(
                    f"{APP_NAME} erzeugt QR-Codes aus Text, speichert sie lokal und überträgt Dateien "
                    "als Folge von QR-Codes zwischen zwei Geräten."
                ),
                muted(f"Version {APP_VERSION}"),
            ),
            section(
                "Entwicklerteam",
                *[paragraph(name) for name in DEVELOPER_TEAM],
            ),
            section(
                "Open-Source-Lizenzen",
                paragraph(f"{APP_NAME} verwendet folgende Open-Source-Software:"),
                name_value_rows(OPEN_SOURCE_LICENSES),
            ),
        ],
    )


# ================== IMPRINT ==================


def imprint_view(page: ft.Page) -> ft.View:
    return settings_page(
        page,
        route=SETTINGS_ROUTES["imprint"],
        title=title_text(("IMPRESSUM", ft.FontWeight.W_700)),
        sections=[
            section(
                "Verantwortlicher / Herausgeber",
                paragraph(APP_PUBLISHER_NAME),
            ),
            section(
                "Kontakt",
                email_link(APP_CONTACT_EMAIL),
            ),
            section(
                "Projekt",
                paragraph(
                    f"{APP_NAME} wird im Rahmen eines Schulprojekts an der FH Technikum Wien veröffentlicht. "
                    "Es steht kein Unternehmen dahinter und es wird kein kommerzieller Zweck verfolgt."
                ),
            ),
        ],
    )
