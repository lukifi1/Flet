"""Log viewer UI component."""

import asyncio
from typing import Optional

import flet as ft

from app.core.constants import UI_PAGE_BG
from app.core.log_handler import get_memory_handler

from . import actions
from .state import LogViewerState


def log_viewer_view(page: ft.Page) -> ft.View:
    """
    Create the log viewer view.

    Args:
        page: The Flet page instance

    Returns:
        A View containing the log viewer UI
    """
    state = LogViewerState.create()

    # UI Components
    filter_dropdown = ft.Dropdown(
        label="Filter by Level",
        options=[ft.dropdown.Option(level) for level in state.log_levels],
        value="ALL",
        width=150,
    )

    log_display = ft.ListView(
        expand=True,
        auto_scroll=state.auto_scroll,
        spacing=4,
        padding=12,
    )

    log_count = ft.Text("Logs: 0", size=12, color=ft.Colors.GREY_700)
    auto_scroll_switch = ft.Switch(
        label="Auto-scroll",
        value=state.auto_scroll,
        scale=0.8,
    )

    def refresh_logs() -> None:
        """Refresh the log display with current filtered logs."""
        try:
            filtered_logs = actions.get_filtered_logs(state)
            log_display.controls.clear()

            # Always show at least the count
            if len(filtered_logs) == 0:
                # Show placeholder if no logs
                log_display.controls.append(
                    ft.Text(
                        "No logs yet. Performing actions will generate logs...",
                        size=12,
                        color=ft.Colors.GREY_700,
                        italic=True,
                    )
                )
            else:
                for log_entry in filtered_logs:
                    color = _get_level_color(log_entry["level"])
                    
                    # Create individual log row
                    log_row = ft.Row(
                        [
                            ft.Text(
                                log_entry["timestamp"],
                                size=10,
                                color=ft.Colors.GREY_800,
                                width=60,
                            ),
                            ft.Text(
                                f"[{log_entry['level']}]",
                                size=10,
                                color=color,
                                weight=ft.FontWeight.W_600,
                                width=75,
                            ),
                            ft.Text(
                                log_entry["message"],
                                size=10,
                                color=ft.Colors.BLACK,
                                expand=True,
                                selectable=True,
                            ),
                        ],
                        spacing=8,
                        wrap=True,
                    )
                    log_display.controls.append(log_row)

            log_count.value = f"Logs: {len(filtered_logs)}"
        except Exception as e:
            log_display.controls.clear()
            log_display.controls.append(
                ft.Text(f"Error refreshing logs: {str(e)}", color=ft.Colors.RED)
            )

    def handle_filter_change(e: ft.Event) -> None:
        """Handle filter dropdown change."""
        state.filter_level = filter_dropdown.value
        refresh_logs()

    def handle_auto_scroll_change(e: ft.Event) -> None:
        """Handle auto-scroll toggle."""
        state.auto_scroll = auto_scroll_switch.value
        log_display.auto_scroll = state.auto_scroll
        try:
            log_display.update()
        except RuntimeError:
            pass

    def handle_clear_logs(e: ft.Event) -> None:
        """Handle clear logs button."""
        actions.clear_logs()
        refresh_logs()

    filter_dropdown.on_change = handle_filter_change
    auto_scroll_switch.on_change = handle_auto_scroll_change

    clear_button = ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_size=18,
        tooltip="Clear logs",
        on_click=handle_clear_logs,
    )

    # Set up periodic refresh
    async def periodic_refresh() -> None:
        """Periodically refresh the log display."""
        await asyncio.sleep(1)  # Wait for page to be ready
        while True:
            await asyncio.sleep(state.refresh_interval)
            try:
                refresh_logs()
                page.update()
            except Exception as e:
                import traceback
                # Silently fail but don't crash
                traceback.print_exc()

    page.run_task(periodic_refresh)

    # Toolbar
    toolbar = ft.Row(
        [
            filter_dropdown,
            ft.VerticalDivider(width=1),
            auto_scroll_switch,
            ft.VerticalDivider(width=1),
            clear_button,
            ft.Container(expand=True),
            log_count,
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
        wrap=True,
    )

    # Main layout
    return ft.View(
        route="/logs",
        controls=[
            ft.SafeArea(
                ft.Column(
                    [
                        ft.Text(
                            "App Logs",
                            size=24,
                            weight=ft.FontWeight.W_700,
                        ),
                        toolbar,
                        ft.Divider(),
                        log_display,
                    ],
                    spacing=12,
                    expand=True,
                ),
                expand=True,
            )
        ],
        padding=16,
        bgcolor=UI_PAGE_BG,
    )


def _get_level_color(level: str) -> str:
    """
    Get the color for a log level.

    Args:
        level: The log level name

    Returns:
        A Flet color string
    """
    colors = {
        "DEBUG": "#0066CC",      # Bright blue
        "VERBOSE": "#00CCCC",    # Bright cyan
        "INFO": "#009900",       # Bright green
        "WARNING": "#FF6600",    # Bright orange
        "ERROR": "#CC0000",      # Bright red
        "CRITICAL": "#990000",   # Dark red
    }
    return colors.get(level, "#666666")
