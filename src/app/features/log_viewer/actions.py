"""Log viewer actions and business logic."""

import logging
from typing import Optional

from app.core.log_handler import get_memory_handler

from .state import LogViewerState


def get_filtered_logs(
    state: LogViewerState,
) -> list[dict]:
    """
    Get logs filtered by the current state filter level.

    Args:
        state: Current log viewer state

    Returns:
        List of filtered log entries
    """
    handler = get_memory_handler()

    if state.filter_level == "ALL":
        return handler.get_logs()

    return handler.get_logs(filter_level=state.filter_level)


def set_filter_level(state: LogViewerState, level: str) -> LogViewerState:
    """
    Update the log level filter.

    Args:
        state: Current log viewer state
        level: New log level filter

    Returns:
        Updated state
    """
    state.filter_level = level
    return state


def toggle_auto_scroll(state: LogViewerState) -> LogViewerState:
    """
    Toggle auto-scroll feature.

    Args:
        state: Current log viewer state

    Returns:
        Updated state
    """
    state.auto_scroll = not state.auto_scroll
    return state


def clear_logs() -> None:
    """Clear all stored logs."""
    handler = get_memory_handler()
    handler.clear_logs()


def get_log_count() -> int:
    """
    Get the total number of stored logs.

    Returns:
        Number of log entries
    """
    handler = get_memory_handler()
    return handler.get_log_count()
