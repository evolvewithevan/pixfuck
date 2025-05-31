from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
    QMessageBox, QComboBox, QSlider, QProgressBar, QSizePolicy, QGridLayout, QGroupBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image
from .worker import PixelSortWorker
from .logger import get_logger

class PixelSortApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_logger('PixelSortApp')
        self.logger.info("Initializing PixelSortApp")
        
        self.setWindowTitle("Enhanced Pixel Sorting App")
        self.setGeometry(50, 50, 1400, 800)

        # Initialize variables to hold images
        self.original_image = None
        self.sorted_image = None

        # Initialize worker thread
        self.worker = None

        # Set up the UI
        self.setup_ui()
        self.logger.info("PixelSortApp initialization complete")

    def setup_ui(self):
        self.logger.debug("Setting up UI components")
        # Main layout
        main_layout = QVBoxLayout()

        # File Operations Group
        file_ops_group = QGroupBox("File Operations")
        file_ops_layout = QHBoxLayout()

        # Load Image Button
        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image)
        file_ops_layout.addWidget(load_button)

        # Save Image Button
        save_button = QPushButton("Save Sorted Image")
        save_button.clicked.connect(self.save_image)
        save_button.setEnabled(False)
        self.save_button = save_button
        file_ops_layout.addWidget(save_button)

        file_ops_group.setLayout(file_ops_layout)
        main_layout.addWidget(file_ops_group)

        # Sorting Options Group
        sorting_options_group = QGroupBox("Sorting Options")
        sorting_layout = QGridLayout()

        # Sort Button
        sort_button = QPushButton("Sort Pixels")
        sort_button.clicked.connect(self.sort_pixels)
        sort_button.setEnabled(False)
        self.sort_button = sort_button
        sorting_layout.addWidget(sort_button, 0, 0, 1, 3)

        # Sorting Angle Slider
        angle_label = QLabel("Sort Angle:")
        sorting_layout.addWidget(angle_label, 1, 0)

        angle_slider = QSlider(Qt.Orientation.Horizontal)
        angle_slider.setMinimum(0)
        angle_slider.setMaximum(359)
        angle_slider.setValue(0)
        angle_slider.setTickInterval(30)
        angle_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.angle_slider = angle_slider
        sorting_layout.addWidget(angle_slider, 1, 1)

        self.angle_value_label = QLabel("0°")
        sorting_layout.addWidget(self.angle_value_label, 1, 2)

        angle_slider.valueChanged.connect(self.update_angle_label)

        # Sorting Criteria
        criteria_label = QLabel("Sort Criterion:")
        sorting_layout.addWidget(criteria_label, 2, 0)

        criteria_combo = QComboBox()
        criteria_combo.addItems(["Brightness", "Hue", "Saturation", "Intensity", "Minimum"])
        self.criteria_combo = criteria_combo
        sorting_layout.addWidget(criteria_combo, 2, 1, 1, 2)

        # Intensity Slider
        intensity_label = QLabel("Intensity:")
        sorting_layout.addWidget(intensity_label, 3, 0)

        intensity_slider = QSlider(Qt.Orientation.Horizontal)
        intensity_slider.setMinimum(1)
        intensity_slider.setMaximum(100)
        intensity_slider.setValue(100)
        intensity_slider.setTickInterval(10)
        intensity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.intensity_slider = intensity_slider
        sorting_layout.addWidget(intensity_slider, 3, 1)

        self.intensity_value_label = QLabel("100%")
        sorting_layout.addWidget(self.intensity_value_label, 3, 2)

        intensity_slider.valueChanged.connect(self.update_intensity_label)

        sorting_options_group.setLayout(sorting_layout)
        main_layout.addWidget(sorting_options_group)

        # Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        self.progress_bar = progress_bar
        main_layout.addWidget(progress_bar)

        # Images layout
        images_layout = QHBoxLayout()

        # Original Image
        original_container = QVBoxLayout()
        self.original_label = QLabel("Original Image")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        original_container.addWidget(self.original_label)
        images_layout.addLayout(original_container)

        # Sorted Image
        sorted_container = QVBoxLayout()
        self.sorted_label = QLabel("Sorted Image")
        self.sorted_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sorted_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sorted_container.addWidget(self.sorted_label)
        images_layout.addLayout(sorted_container)

        main_layout.addLayout(images_layout)

        # Set the central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Allow the window to be resized
        self.setMinimumSize(800, 600)

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
        label.setPixmap(pixmap.scaled(
            label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

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
        self.sorted_image = sorted_image
        self.display_image(sorted_image, self.sorted_label)
        self.sort_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.worker = None

    def on_sort_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred during sorting:\n{error_message}")
        self.sort_button.setEnabled(True)
        self.worker = None

    def save_image(self):
        if self.sorted_image is None:
            QMessageBox.warning(self, "Warning", "No sorted image to save.")
            return
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Sorted Image", "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;BMP Files (*.bmp);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                self.sorted_image.save(file_name)
                QMessageBox.information(self, "Success", "Image saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}") 