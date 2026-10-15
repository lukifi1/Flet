import traceback

import flet as ft
import asyncio

from app.core.constants import (
    UI_FONT_FAMILY,
    UI_FONT_FILE,
    UI_NAV_BG,
    UI_NAV_ICON_SELECTED,
    UI_NAV_ICON_UNSELECTED,
    UI_NAV_INDICATOR_BG,
    UI_NAV_TEXT_SELECTED,
    UI_NAV_TEXT_UNSELECTED,
    UI_PAGE_BG,
    UI_PAGE_TRANSITION_ANIMATION,
)
from app.router import build_view
from app.core.logger import get_logger
from app.core.share_intent import consume_payloads, file_qr_data

log = get_logger(__name__)

def main(page: ft.Page):
    page.title = "QR Maker"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0
    page.bgcolor = UI_PAGE_BG
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.fonts = {UI_FONT_FAMILY: UI_FONT_FILE}
    page.theme = ft.Theme(
        font_family=UI_FONT_FAMILY,
        navigation_bar_theme=ft.NavigationBarTheme(
            label_text_style={
                ft.ControlState.SELECTED: ft.TextStyle(
                    color=UI_NAV_TEXT_SELECTED,
                    weight=ft.FontWeight.W_600,
                ),
                ft.ControlState.DEFAULT: ft.TextStyle(
                    color=UI_NAV_TEXT_UNSELECTED,
                    weight=ft.FontWeight.W_500,
                ),
            }
        ),
        page_transitions=ft.PageTransitionsTheme(
            android=UI_PAGE_TRANSITION_ANIMATION,
            ios=UI_PAGE_TRANSITION_ANIMATION,
            linux=UI_PAGE_TRANSITION_ANIMATION,
            macos=UI_PAGE_TRANSITION_ANIMATION,
            windows=UI_PAGE_TRANSITION_ANIMATION,
        ),
    )
    
    # ================== NAV BAR ==================

    nav_bar = ft.NavigationBar(
        bgcolor=UI_NAV_BG,
        indicator_color=UI_NAV_INDICATOR_BG,
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.HOME_OUTLINED, color=UI_NAV_ICON_UNSELECTED),
                selected_icon=ft.Icon(ft.Icons.HOME, color=UI_NAV_ICON_SELECTED),
                label="Home",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.QR_CODE_2_OUTLINED, color=UI_NAV_ICON_UNSELECTED),
                selected_icon=ft.Icon(ft.Icons.QR_CODE_2, color=UI_NAV_ICON_SELECTED),
                label="My Codes",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.TERMINAL_OUTLINED, color=UI_NAV_ICON_UNSELECTED),
                selected_icon=ft.Icon(ft.Icons.TERMINAL, color=UI_NAV_ICON_SELECTED),
                label="Logs",
            ),
        ],
    )

    syncing_nav_state = False
    nav_push_in_flight = False

    async def push_route_guarded(target_route: str):
        nonlocal nav_push_in_flight
        if nav_push_in_flight:
            return
        nav_push_in_flight = True
        try:
            await page.push_route(target_route)
        finally:
            nav_push_in_flight = False

    def set_nav_state(route: str):
        nonlocal syncing_nav_state
        route_to_index = {
            "/": 0,
            "/my-codes": 1,
            "/logs": 2,
        }
        target_index = route_to_index.get(route, 0)
        if nav_bar.selected_index != target_index:
            syncing_nav_state = True
            nav_bar.selected_index = target_index
            syncing_nav_state = False

    def handle_nav_change(e: ft.Event[ft.NavigationBar]):
        nonlocal syncing_nav_state
        if syncing_nav_state:
            return
        index_to_route = {
            0: "/",
            1: "/my-codes",
            2: "/logs",
        }
        target_route = index_to_route.get(nav_bar.selected_index, "/")
        if page.route != target_route:
            page.run_task(push_route_guarded, target_route)

    nav_bar.on_change = handle_nav_change

    async def poll_share_intent():
        log.info("Android share inbox receiver ready")
        while True:
            try:
                for payload in consume_payloads():
                    files = page.session.store.get("shared_files") or []
                    messages = []
                    text = payload.get("text") or ""
                    for item in payload.get("files", []):
                        try:
                            shared_file_text = file_qr_data(item)
                        except (OSError, ValueError) as exc:
                            messages.append(str(exc))
                            log.warning("Shared file rejected: %s", exc)
                            continue
                        files.append(item)
                        messages.append(f"Received and read {item['name']} ({item['size']} bytes)")
                        log.info("Shared file read: name=%s size=%s path=%s", item["name"], item["size"], item["path"])
                        if len(payload["files"]) == 1:
                            text = shared_file_text
                    for error in payload.get("errors", []):
                        log.error("Share reception: %s", error)
                        messages.append(error)
                    if text:
                        page.qr_input_text = text
                        log.info("Received shared text (%d characters)", len(text))
                        if not messages:
                            messages.append(f"Received shared text ({len(text)} characters)")
                    page.session.store.set("shared_files", files)
                    page.session.store.set("share_debug", "\n".join(messages))
                    if page.route != "/":
                        await page.push_route("/")
                    else:
                        render_current_route()
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Failed to process shared payload")
                await asyncio.sleep(2)

    share_task = None
    def stop_share_poller(e):
        if share_task is not None:
            share_task.cancel()
    page.on_disconnect = stop_share_poller

    def render_current_route() -> None:
        try:
            current_view = build_view(page)
            current_view.navigation_bar = nav_bar
            page.views.clear()
            page.views.append(current_view)
            set_nav_state(page.route)
        except Exception as exc:
            # Surface route/render failures directly in UI instead of hanging on white page.
            page.views.clear()
            page.views.append(
                ft.View(
                    controls=[
                        ft.SafeArea(
                            ft.Container(
                                padding=20,
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "App failed to render",
                                            size=22,
                                            weight=ft.FontWeight.W_700,
                                            color=ft.Colors.RED_700,
                                        ),
                                        ft.Text(str(exc), size=14),
                                        ft.Text(traceback.format_exc(), size=12),
                                    ],
                                    spacing=12,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                            )
                        )
                    ],
                )
            )
        page.update()

    def handle_route_change(e: ft.RouteChangeEvent):
        render_current_route()

    page.on_route_change = handle_route_change
    page.route = page.route or "/"
    render_current_route()

    if page.platform == ft.PagePlatform.ANDROID and not page.web:
        share_task = page.run_task(poll_share_intent)
