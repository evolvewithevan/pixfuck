import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from ui import PixelSortApp
from ui.logger import setup_logger, get_logger

def main():
    # Setup logging
    logger = setup_logger()
    app_logger = get_logger('main')
    
    try:
        app_logger.info("Starting application...")
        app_logger.debug(f"Display: {os.environ.get('DISPLAY')}")
        app_logger.debug(f"Wayland Display: {os.environ.get('WAYLAND_DISPLAY')}")
        app_logger.debug(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM')}")
        
        app = QApplication(sys.argv)
        app_logger.info("QApplication created")
        app_logger.debug(f"Available platforms: {QApplication.platformName()}")
        
        window = PixelSortApp()
        app_logger.info("Window created")
        window.show()
        app_logger.info("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        app_logger.error(f"Error: {str(e)}")
        app_logger.error("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
