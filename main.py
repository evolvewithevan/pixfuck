import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from ui import PixelSortApp
from ui.logger import setup_logger, get_logger

def log_environment_info(logger):
    """Log relevant environment information for debugging."""
    logger.debug(f"Display: {os.environ.get('DISPLAY')}")
    logger.debug(f"Wayland Display: {os.environ.get('WAYLAND_DISPLAY')}")
    logger.debug(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM')}")

def initialize_application(logger):
    """Initialize and return the QApplication instance."""
    app = QApplication(sys.argv)
    logger.info("QApplication created")
    logger.debug(f"Available platforms: {QApplication.platformName()}")
    return app

def create_main_window(logger):
    """Create and return the main application window."""
    window = PixelSortApp()
    logger.info("Window created")
    return window

def handle_error(logger, error):
    """Handle application errors and log them appropriately."""
    logger.error(f"Error: {str(error)}")
    logger.error("Traceback:", exc_info=True)
    sys.exit(1)

def run_application():
    """Main application runner function."""
    logger = setup_logger()
    app_logger = get_logger('main')
    
    try:
        app_logger.info("Starting application...")
        log_environment_info(app_logger)
        
        app = initialize_application(app_logger)
        window = create_main_window(app_logger)
        
        window.show()
        app_logger.info("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        handle_error(app_logger, e)

if __name__ == "__main__":
    run_application()
