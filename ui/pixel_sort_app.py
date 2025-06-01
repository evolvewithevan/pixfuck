import os
import psutil
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QLabel, QSpinBox, QProgressDialog
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PyQt6 import uic
from PIL import Image, UnidentifiedImageError
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
        self.angle_slider.valueChanged.connect(self.update_angle_spinbox)
        self.intensity_slider.valueChanged.connect(self.update_intensity_spinbox)
        self.angle_value_label.valueChanged.connect(self.update_angle_slider)
        self.intensity_value_label.valueChanged.connect(self.update_intensity_slider)

    def update_intensity_spinbox(self, value):
        self.logger.debug(f"Updating intensity spinbox to {value}%")
        self.intensity_value_label.setValue(value)

    def update_angle_spinbox(self, value):
        self.logger.debug(f"Updating angle spinbox to {value}°")
        self.angle_value_label.setValue(value)

    def update_intensity_slider(self, value):
        self.logger.debug(f"Updating intensity slider to {value}%")
        self.intensity_slider.setValue(value)

    def update_angle_slider(self, value):
        self.logger.debug(f"Updating angle slider to {value}°")
        self.angle_slider.setValue(value)

    def validate_image_size(self, image_path):
        """Validate if the image size is within acceptable limits."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                # Calculate approximate memory usage (3 bytes per pixel for RGB)
                memory_usage = width * height * 3
                # Get available system memory
                available_memory = psutil.virtual_memory().available
                
                # Check if image is too large (more than 50% of available memory)
                if memory_usage > available_memory * 0.5:
                    return False, f"Image is too large ({width}x{height}). Please use a smaller image."
                
                # Check if dimensions are too large
                if width > 10000 or height > 10000:
                    return False, f"Image dimensions ({width}x{height}) exceed maximum allowed size (10000x10000)."
                
                return True, None
        except Exception as e:
            return False, f"Error validating image: {str(e)}"

    def load_image(self):
        """Load an image with enhanced error handling and validation."""
        self.logger.info("Opening file dialog to load image")
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "",
            "Images (*.png *.xpm *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
            options=options
        )
        
        if not file_name:
            return

        try:
            # Validate file exists and is readable
            if not os.path.isfile(file_name):
                raise FileNotFoundError(f"File not found: {file_name}")
            
            if not os.access(file_name, os.R_OK):
                raise PermissionError(f"Cannot read file: {file_name}")

            # Validate image size and memory requirements
            is_valid, error_msg = self.validate_image_size(file_name)
            if not is_valid:
                QMessageBox.critical(self, "Error", error_msg)
                return

            # Show loading progress dialog
            progress = QProgressDialog("Loading image...", None, 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Loading")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()

            self.logger.info(f"Loading image from: {file_name}")
            
            # Load image with progress updates
            with Image.open(file_name) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    image = img.convert('RGB')
                else:
                    image = img.copy()
            progress.setValue(30)
            
            # Store the original image
            self.original_image = image
            progress.setValue(60)
            
            # Display the image
            self.display_image(image, self.original_label)
            progress.setValue(90)
            
            # Reset UI state
            self.sorted_label.clear()
            self.sorted_label.setText("Sorted Image")
            self.sort_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.progress_bar.setValue(0)
            
            progress.setValue(100)
            self.logger.info("Image loaded successfully")
            
        except UnidentifiedImageError:
            self.logger.error(f"Invalid image format: {file_name}")
            QMessageBox.critical(self, "Error", "The selected file is not a valid image format.")
        except FileNotFoundError as e:
            self.logger.error(str(e))
            QMessageBox.critical(self, "Error", str(e))
        except PermissionError as e:
            self.logger.error(str(e))
            QMessageBox.critical(self, "Error", str(e))
        except MemoryError:
            self.logger.error("Not enough memory to load the image")
            QMessageBox.critical(self, "Error", "Not enough memory to load the image. Please try a smaller image.")
        except Exception as e:
            self.logger.error(f"Failed to load image: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{str(e)}")
        finally:
            if 'progress' in locals():
                progress.close()

    def display_image(self, image, label):
        """Display an image in a label while maintaining aspect ratio."""
        self.logger.debug(f"Displaying image of size {image.size}")
        try:
            # Convert PIL Image to QImage
            qimage = self.pil_to_qimage(image)
            if qimage.isNull():
                self.logger.error("Failed to convert PIL image to QImage")
                return

            # Create pixmap from QImage
            pixmap = QPixmap.fromImage(qimage)
            if pixmap.isNull():
                self.logger.error("Failed to create QPixmap from QImage")
                return

            # Get label size
            label_size = label.size()
            
            # Calculate scaling factors
            w_scale = label_size.width() / pixmap.width()
            h_scale = label_size.height() / pixmap.height()
            
            # Use the smaller scale to maintain aspect ratio
            scale = min(w_scale, h_scale)
            
            # Calculate new dimensions
            new_width = int(pixmap.width() * scale)
            new_height = int(pixmap.height() * scale)
            
            # Scale the pixmap
            scaled_pixmap = pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the pixmap in the label
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"Error displaying image: {str(e)}", exc_info=True)

    def pil_to_qimage(self, image):
        """Convert PIL Image to QImage with proper format handling."""
        self.logger.debug("Converting PIL image to QImage")
        try:
            # Ensure image is in RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get image data
            data = image.tobytes("raw", "RGB")
            
            # Create QImage with proper format
            qimage = QImage(
                data,
                image.width,
                image.height,
                image.width * 3,  # stride
                QImage.Format.Format_RGB888
            )
            
            # Create a deep copy to ensure data ownership
            return qimage.copy()
            
        except Exception as e:
            self.logger.error(f"Error converting PIL image to QImage: {str(e)}", exc_info=True)
            return QImage()

    def resizeEvent(self, event):
        self.logger.debug("Window resize event triggered")
        # Refresh images on window resize
        if self.original_image:
            self.display_image(self.original_image, self.original_label)
        if self.sorted_image:
            self.display_image(self.sorted_image, self.sorted_label)
        super().resizeEvent(event)

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
        pattern = self.pattern_combo.currentText()
        intensity = self.intensity_slider.value() / 100.0

        # Start the worker thread
        self.worker = PixelSortWorker(self.original_image, angle, criterion, pattern, intensity)
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