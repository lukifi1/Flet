import flet as ft

from app.app import main
from app.core.config import LOGGING_LEVEL
from app.core.logger import setup_logging

if __name__ == "__main__":
    # Initialize logging
    setup_logging(level=LOGGING_LEVEL)
    ft.run(main, assets_dir="assets")
