"""
In-memory logging handler for real-time log viewer.
Stores recent log entries in a circular buffer for UI display.
"""

import logging
import time
from collections import deque
from typing import Optional


class MemoryLogHandler(logging.Handler):
    """
    Handler that stores log records in memory for UI display.
    Maintains a circular buffer of the most recent logs.
    """

    def __init__(self, max_logs: int = 500):
        """
        Initialize the handler.

        Args:
            max_logs: Maximum number of log entries to keep in memory
        """
        super().__init__()
        self.max_logs = max_logs
        self.logs: deque = deque(maxlen=max_logs)
        self._formatter: Optional[logging.Formatter] = None

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record by storing it in the buffer.

        Args:
            record: The log record to store
        """
        try:
            # Get the formatted message
            msg = self.format(record) if self.formatter else record.getMessage()
            
            # Format timestamp
            timestamp = time.strftime("%H:%M:%S", time.localtime(record.created))
            
            # Store the log entry
            self.logs.append(
                {
                    "level": record.levelname,
                    "message": msg,
                    "timestamp": timestamp,
                    "logger": record.name,
                }
            )
        except Exception as e:
            # Store error info in logs so we can debug
            try:
                self.logs.append(
                    {
                        "level": "ERROR",
                        "message": f"Log handler error: {str(e)}",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "logger": "log_handler",
                    }
                )
            except Exception:
                pass

    def get_logs(self, filter_level: Optional[str] = None) -> list[dict]:
        """
        Get all stored logs, optionally filtered by level.

        Args:
            filter_level: Optional log level to filter by (e.g., 'ERROR', 'WARNING')

        Returns:
            List of log dictionaries
        """
        if filter_level is None:
            return list(self.logs)
        return [log for log in self.logs if log["level"] == filter_level]

    def clear_logs(self) -> None:
        """Clear all stored logs."""
        self.logs.clear()

    def get_log_count(self) -> int:
        """Get the number of stored logs."""
        return len(self.logs)


# Global instance for app-wide access
_memory_handler: Optional[MemoryLogHandler] = None


def get_memory_handler() -> MemoryLogHandler:
    """
    Get the global memory handler instance.

    Returns:
        The memory handler instance
    """
    global _memory_handler
    if _memory_handler is None:
        _memory_handler = MemoryLogHandler()
    return _memory_handler
