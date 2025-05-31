import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from ui import PixelSortApp

def main():
    try:
        print("Starting application...")
        print(f"Display: {os.environ.get('DISPLAY')}")
        print(f"Wayland Display: {os.environ.get('WAYLAND_DISPLAY')}")
        print(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM')}")
        
        app = QApplication(sys.argv)
        print("QApplication created")
        print(f"Available platforms: {QApplication.platformName()}")
        
        window = PixelSortApp()
        print("Window created")
        window.show()
        print("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
