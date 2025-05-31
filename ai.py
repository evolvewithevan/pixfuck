import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
    QMessageBox, QComboBox, QRadioButton, QButtonGroup,
    QSlider, QProgressBar, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image, ImageEnhance
import numpy as np
import colorsys

class PixelSortWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(Image.Image)
    error = pyqtSignal(str)

    def __init__(self, image, direction, criterion, intensity):
        super().__init__()
        self.image = image
        self.direction = direction
        self.criterion = criterion
        self.intensity = intensity

    def run(self):
        try:
            sorted_image = self.pixel_sort(self.image, self.direction, self.criterion, self.intensity)
            self.finished.emit(sorted_image)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{str(e)}\n{tb}")

    def pixel_sort(self, image, direction, criterion, intensity):
        # Convert image to NumPy array
        img_array = np.array(image)
        height, width, channels = img_array.shape

        # Calculate sorting percentage based on intensity
        total_pixels = height * width
        pixels_to_sort = int(total_pixels * intensity)

        # Depending on direction, define lines to sort
        if direction == 'Horizontal':
            lines = height
            sort_axis = 1  # Sort each row
        else:
            lines = width
            sort_axis = 0  # Sort each column

        sorted_array = img_array.copy()

        for i in range(lines):
            if direction == 'Horizontal':
                line = sorted_array[i, :, :].copy()
            else:
                line = sorted_array[:, i, :].copy()

            # Calculate sorting key based on criterion
            if criterion == 'Brightness':
                key = line.mean(axis=1) if direction == 'Horizontal' else line.mean(axis=1)
            elif criterion == 'Hue':
                hsv = np.array([colorsys.rgb_to_hsv(*pixel/255.0) for pixel in line])
                key = hsv[:, 0]  # Hue
            elif criterion == 'Saturation':
                hsv = np.array([colorsys.rgb_to_hsv(*pixel/255.0) for pixel in line])
                key = hsv[:, 1]  # Saturation
            else:
                key = line.mean(axis=1)

            # Get sorting indices
            sorted_indices = np.argsort(key)
            sorted_line = line[sorted_indices]

            # Apply sorting based on intensity
            if intensity < 1.0:
                num_pixels = int(len(sorted_line) * intensity)
                if direction == 'Horizontal':
                    sorted_array[i, :num_pixels, :] = sorted_line[:num_pixels]
                else:
                    sorted_array[:num_pixels, i, :] = sorted_line[:num_pixels]
            else:
                if direction == 'Horizontal':
                    sorted_array[i, :, :] = sorted_line
                else:
                    sorted_array[:, i, :] = sorted_line

            # Update progress
            progress_percent = int(((i + 1) / lines) * 100)
            self.progress.emit(progress_percent)

        # Convert back to PIL Image
        sorted_image = Image.fromarray(sorted_array)
        return sorted_image

class PixelSortApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Pixel Sorting App")
        self.setGeometry(50, 50, 1400, 800)

        # Initialize variables to hold images
        self.original_image = None
        self.sorted_image = None

        # Initialize worker thread
        self.worker = None

        # Set up the UI
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Buttons and Controls layout
        controls_layout = QHBoxLayout()

        # Load Image Button
        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image)
        controls_layout.addWidget(load_button)

        # Save Image Button
        save_button = QPushButton("Save Sorted Image")
        save_button.clicked.connect(self.save_image)
        save_button.setEnabled(False)
        self.save_button = save_button
        controls_layout.addWidget(save_button)

        # Sort Button
        sort_button = QPushButton("Sort Pixels")
        sort_button.clicked.connect(self.sort_pixels)
        sort_button.setEnabled(False)
        self.sort_button = sort_button
        controls_layout.addWidget(sort_button)

        # Sorting Direction
        direction_layout = QHBoxLayout()
        direction_label = QLabel("Sort Direction:")
        direction_layout.addWidget(direction_label)

        self.direction_group = QButtonGroup(self)

        horizontal_radio = QRadioButton("Horizontal")
        horizontal_radio.setChecked(True)
        self.direction_group.addButton(horizontal_radio)
        direction_layout.addWidget(horizontal_radio)

        vertical_radio = QRadioButton("Vertical")
        self.direction_group.addButton(vertical_radio)
        direction_layout.addWidget(vertical_radio)

        controls_layout.addLayout(direction_layout)

        # Sorting Criteria
        criteria_layout = QHBoxLayout()
        criteria_label = QLabel("Sort Criterion:")
        criteria_layout.addWidget(criteria_label)

        criteria_combo = QComboBox()
        criteria_combo.addItems(["Brightness", "Hue", "Saturation"])
        self.criteria_combo = criteria_combo
        criteria_layout.addWidget(criteria_combo)

        controls_layout.addLayout(criteria_layout)

        # Intensity Slider
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("Intensity:")
        intensity_layout.addWidget(intensity_label)

        intensity_slider = QSlider(Qt.Horizontal)
        intensity_slider.setMinimum(1)
        intensity_slider.setMaximum(100)
        intensity_slider.setValue(100)
        intensity_slider.setTickInterval(10)
        intensity_slider.setTickPosition(QSlider.TicksBelow)
        self.intensity_slider = intensity_slider
        intensity_layout.addWidget(intensity_slider)

        self.intensity_value_label = QLabel("100%")
        intensity_layout.addWidget(self.intensity_value_label)

        intensity_slider.valueChanged.connect(self.update_intensity_label)

        controls_layout.addLayout(intensity_layout)

        main_layout.addLayout(controls_layout)

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
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        original_scroll = QWidget()
        original_scroll_layout = QVBoxLayout()
        original_scroll_layout.addWidget(self.original_label)
        original_scroll.setLayout(original_scroll_layout)

        original_wrapper = QWidget()
        original_wrapper.setLayout(original_scroll_layout)
        images_layout.addWidget(original_wrapper)

        # Sorted Image
        sorted_container = QVBoxLayout()
        self.sorted_label = QLabel("Sorted Image")
        self.sorted_label.setAlignment(Qt.AlignCenter)
        self.sorted_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sorted_scroll = QWidget()
        sorted_scroll_layout = QVBoxLayout()
        sorted_scroll_layout.addWidget(self.sorted_label)
        sorted_scroll.setLayout(sorted_scroll_layout)

        sorted_wrapper = QWidget()
        sorted_wrapper.setLayout(sorted_scroll_layout)
        images_layout.addWidget(sorted_wrapper)

        main_layout.addLayout(images_layout)

        # Set the central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def update_intensity_label(self, value):
        self.intensity_value_label.setText(f"{value}%")

    def load_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "",
            "Images (*.png *.xpm *.jpg *.bmp *.gif);;All Files (*)",
            options=options
        )
        if file_name:
            try:
                image = Image.open(file_name).convert("RGB")
                self.original_image = image
                self.display_image(image, self.original_label)
                self.sorted_label.clear()
                self.sorted_label.setText("Sorted Image")
                self.sort_button.setEnabled(True)
                self.save_button.setEnabled(False)
                self.progress_bar.setValue(0)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")

    def display_image(self, image, label):
        # Convert PIL Image to QImage
        qimage = self.pil_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)

        # Scale pixmap to fit the label while maintaining aspect ratio
        label.setPixmap(pixmap.scaled(
            label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def resizeEvent(self, event):
        # Refresh images on window resize
        if self.original_image:
            self.display_image(self.original_image, self.original_label)
        if self.sorted_image:
            self.display_image(self.sorted_image, self.sorted_label)
        super().resizeEvent(event)

    def pil_to_qimage(self, image):
        data = image.tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)
        return qimage

    def sort_pixels(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Warning", "No image loaded to sort.")
            return

        # Disable buttons to prevent multiple operations
        self.sort_button.setEnabled(False)
        self.save_button.setEnabled(False)

        # Get sorting parameters
        direction = 'Horizontal' if self.direction_group.checkedButton().text() == 'Horizontal' else 'Vertical'
        criterion = self.criteria_combo.currentText()
        intensity = self.intensity_slider.value() / 100.0

        # Start the worker thread
        self.worker = PixelSortWorker(self.original_image, direction, criterion, intensity)
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
        options = QFileDialog.Options()
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

def main():
    app = QApplication(sys.argv)
    window = PixelSortApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
