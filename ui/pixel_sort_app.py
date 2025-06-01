from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PyQt6 import uic
from PIL import Image
from .worker import PixelSortWorker
from .logger import get_logger

class PixelSortApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_logger('PixelSortApp')
        self.logger.info("Initializing PixelSortApp")
        
        # Load the UI file
        uic.loadUi('ui/main_window.ui', self)
        
        # Initialize variables to hold images
        self.original_image = None
        self.sorted_image = None

        # Initialize worker thread
        self.worker = None

        # Set up image labels
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sorted_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setMinimumSize(400, 300)
        self.sorted_label.setMinimumSize(400, 300)

        # Connect signals
        self.setup_connections()
        self.logger.info("PixelSortApp initialization complete")

    def setup_connections(self):
        self.logger.debug("Setting up signal connections")
        self.load_button.clicked.connect(self.load_image)
        self.save_button.clicked.connect(self.save_image)
        self.sort_button.clicked.connect(self.sort_pixels)
        self.angle_slider.valueChanged.connect(self.update_angle_label)
        self.intensity_slider.valueChanged.connect(self.update_intensity_label)

    def update_intensity_label(self, value):
        self.logger.debug(f"Updating intensity label to {value}%")
        self.intensity_value_label.setText(f"{value}%")

    def update_angle_label(self, value):
        self.logger.debug(f"Updating angle label to {value}°")
        self.angle_value_label.setText(f"{value}°")

    def load_image(self):
        self.logger.info("Opening file dialog to load image")
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "",
            "Images (*.png *.xpm *.jpg *.bmp *.gif);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                self.logger.info(f"Loading image from: {file_name}")
                image = Image.open(file_name).convert("RGB")
                self.original_image = image
                self.display_image(image, self.original_label)
                self.sorted_label.clear()
                self.sorted_label.setText("Sorted Image")
                self.sort_button.setEnabled(True)
                self.save_button.setEnabled(False)
                self.progress_bar.setValue(0)
                self.logger.info("Image loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load image: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")

    def display_image(self, image, label):
        self.logger.debug(f"Displaying image of size {image.size}")
        # Convert PIL Image to QImage
        qimage = self.pil_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)

        # Scale pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            label.width(),
            label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        self.logger.debug("Window resize event triggered")
        # Refresh images on window resize
        if self.original_image:
            self.display_image(self.original_image, self.original_label)
        if self.sorted_image:
            self.display_image(self.sorted_image, self.sorted_label)
        super().resizeEvent(event)

    def pil_to_qimage(self, image):
        self.logger.debug("Converting PIL image to QImage")
        data = image.tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
        return qimage

    def sort_pixels(self):
        if self.original_image is None:
            self.logger.warning("Attempted to sort pixels without loading an image")
            QMessageBox.warning(self, "Warning", "No image loaded to sort.")
            return

        self.logger.info("Starting pixel sorting operation")
        # Disable buttons to prevent multiple operations
        self.sort_button.setEnabled(False)
        self.save_button.setEnabled(False)

        # Get sorting parameters
        angle = self.angle_slider.value()
        criterion = self.criteria_combo.currentText()
        intensity = self.intensity_slider.value() / 100.0

        # Start the worker thread
        self.worker = PixelSortWorker(self.original_image, angle, criterion, intensity)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_sort_finished)
        self.worker.error.connect(self.on_sort_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_sort_finished(self, sorted_image):
        self.logger.info("Sorting finished, displaying result")
        self.sorted_image = sorted_image
        self.display_image(sorted_image, self.sorted_label)
        self.sort_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.worker = None

    def on_sort_error(self, error_message):
        self.logger.error(f"Sorting error: {error_message}")
        QMessageBox.critical(self, "Error", f"An error occurred during sorting:\n{error_message}")
        self.sort_button.setEnabled(True)
        self.worker = None

    def save_image(self):
        if self.sorted_image is None:
            QMessageBox.warning(self, "Warning", "No sorted image to save.")
            return
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Image File", "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;BMP Image (*.bmp);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                self.logger.info(f"Saving image to: {file_name}")
                self.sorted_image.save(file_name)
                self.logger.info("Image saved successfully")
            except Exception as e:
                self.logger.error(f"Failed to save image: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}") 