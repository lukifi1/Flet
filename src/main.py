import flet as ft
import logging

from app.app import main
from app.core.config import LOGGING_LEVEL
from app.core.logger import setup_logging

if __name__ == "__main__":
    # Initialize logging
    setup_logging(level=LOGGING_LEVEL)
    
    # Get a logger and log startup
    log = logging.getLogger("qr_maker")
    log.info("════════════════════════════════════════════")
    log.info("APPLICATION STARTED")
    log.info("════════════════════════════════════════════")
    
    ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
