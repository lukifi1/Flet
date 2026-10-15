"""Log viewer state management."""

import logging
from dataclasses import dataclass, field


@dataclass
class LogViewerState:
    """State for the log viewer feature."""

    filter_level: str = "ALL"
    """Current log level filter (ALL, DEBUG, INFO, WARNING, ERROR, CRITICAL)"""

    auto_scroll: bool = True
    """Whether to automatically scroll to the latest log"""

    refresh_interval: float = 0.5
    """Interval in seconds for refreshing the log display"""

    log_levels: list[str] = field(
        default_factory=lambda: ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    """Available log level filters"""

    @classmethod
    def create(cls) -> "LogViewerState":
        """
        Create a new log viewer state instance.

        Returns:
            New LogViewerState instance
        """
        return cls()
