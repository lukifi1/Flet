"""
Logging configuration module for QR Code Generator.
Provides structured logging across the application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Optional, cast

VERBOSE_LEVEL = 5


class VerboseLogger(logging.Logger):
    """Application logger with a custom VERBOSE level helper."""

    def verbose(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kwargs)


def _register_verbose_level() -> None:
    """Register a custom VERBOSE level and convenience logger methods."""
    if logging.getLevelName(VERBOSE_LEVEL) != "VERBOSE":
        logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")

    if logging.getLoggerClass() is not VerboseLogger:
        logging.setLoggerClass(VerboseLogger)

    if not hasattr(logging.Logger, "verbose"):

        def verbose(
            self: logging.Logger, message: str, *args: Any, **kwargs: Any
        ) -> None:
            if self.isEnabledFor(VERBOSE_LEVEL):
                self._log(VERBOSE_LEVEL, message, args, **kwargs)

        setattr(logging.Logger, "verbose", verbose)

    if not hasattr(logging, "verbose"):

        def verbose_root(message: str, *args: Any, **kwargs: Any) -> None:
            logging.log(VERBOSE_LEVEL, message, *args, **kwargs)

        setattr(logging, "verbose", verbose_root)


_register_verbose_level()


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output with level-based styling.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "VERBOSE": "\033[94m",  # Bright Blue
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
    }
    PREFIX_WIDTH = 3
    LEVEL_WIDTH = 8

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and enhanced visible separators."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = self.formatTime(record, "%H:%M:%S")

        # Keep visual columns aligned across log levels.
        prefix_map = {
            "DEBUG": "[*]",
            "VERBOSE": "[v]",
            "INFO": "[i]",
            "WARNING": "[!]",
            "ERROR": "[x]",
            "CRITICAL": "[💀]",
        }
        prefix = prefix_map.get(levelname, "[ ]")
        padded_prefix = f"{prefix:<{self.PREFIX_WIDTH}}"
        padded_level = f"{levelname:<{self.LEVEL_WIDTH}}"

        colored_prefix = f"{color}{padded_prefix}{reset}"
        colored_levelname = f"{color}{padded_level}{reset}"

        # Add visual separators for important levels
        if levelname in ("ERROR", "CRITICAL"):
            separator = f"{color}{'=' * 60}{reset}"
            message = (
                f"{separator}\n"
                f"[{timestamp}] {colored_prefix} {colored_levelname} - {record.getMessage()}\n"
                f"{separator}"
            )
        else:
            message = f"[{timestamp}] {colored_prefix} {colored_levelname} - {record.getMessage()}"

        return message


def setup_logging(
    log_dir: Optional[Path] = None, level: int = logging.INFO
) -> VerboseLogger:
    """
    Configure application logging with file and console handlers.

    Args:
        log_dir: Directory to store log files. Defaults to project data/logs/
        level: Logging level (default: logging.INFO)

    Returns:
        Configured logger instance
    """
    _register_verbose_level()

    if log_dir is None:
        log_dir = Path(__file__).resolve().parents[3] / "data" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = cast(VerboseLogger, logging.getLogger("qr_maker"))
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler (INFO and above) with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(
        logging.DEBUG
    )  # Capture all levels, formatter controls output
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)

    # File handler (DEBUG and above)
    log_file = log_dir / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized: console + file logs to {log_file}")

    return logger


def get_logger(name: str = "qr_maker") -> VerboseLogger:
    """Get the configured logger instance."""
    # Ensure all module loggers are children of 'qr_maker' so they share handlers.
    logger_name = name if name.startswith("qr_maker") else f"qr_maker.{name}"
    return cast(VerboseLogger, logging.getLogger(logger_name))
