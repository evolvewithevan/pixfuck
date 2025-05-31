import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
    QMessageBox, QComboBox, QSlider, QProgressBar, QSizePolicy, QGridLayout, QGroupBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import numpy as np
from numba import njit
import scipy.ndimage

# Numba-compatible RGB to HSV conversion
@njit
def rgb_to_hsv_numba(r, g, b):
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    delta = maxc - minc
    h = np.zeros_like(maxc, dtype=np.float32)
    s = np.zeros_like(maxc, dtype=np.float32)
    v = maxc.astype(np.float32)

    mask = delta != 0
    s[mask] = delta[mask] / maxc[mask]

    rc = np.zeros_like(maxc, dtype=np.float32)
    gc = np.zeros_like(maxc, dtype=np.float32)
    bc = np.zeros_like(maxc, dtype=np.float32)
    rc[mask] = (maxc[mask] - r[mask]) / delta[mask]
    gc[mask] = (maxc[mask] - g[mask]) / delta[mask]
    bc[mask] = (maxc[mask] - b[mask]) / delta[mask]

    cond_r = (r == maxc) & mask
    cond_g = (g == maxc) & mask
    cond_b = (b == maxc) & mask

    h[cond_r] = bc[cond_r] - gc[cond_r]
    h[cond_g] = np.float32(2.0) + rc[cond_g] - bc[cond_g]
    h[cond_b] = np.float32(4.0) + gc[cond_b] - rc[cond_b]

    h = (h / np.float32(6.0)) % np.float32(1.0)
    h[~mask] = np.float32(0.0)

    return h, s, v

@njit
def row_max(arr):
    n_rows, n_cols = arr.shape
    result = np.empty(n_rows, dtype=arr.dtype)
    for i in range(n_rows):
        max_val = arr[i, 0]
        for j in range(1, n_cols):
            if arr[i, j] > max_val:
                max_val = arr[i, j]
        result[i] = max_val
    return result

@njit
def row_min(arr):
    n_rows, n_cols = arr.shape
    result = np.empty(n_rows, dtype=arr.dtype)
    for i in range(n_rows):
        min_val = arr[i, 0]
        for j in range(1, n_cols):
            if arr[i, j] < min_val:
                min_val = arr[i, j]
            result[i] = min_val
    return result

@njit
def process_line(line, criterion_id):
    length = line.shape[0]
    key = np.empty(length, dtype=np.float32)
    line = line.astype(np.float32)
    if criterion_id == 0:
        for j in range(length):
            key[j] = (line[j, 0] + line[j, 1] + line[j, 2]) / np.float32(3.0)
    elif criterion_id == 1:
        r = line[:, 0] / np.float32(255.0)
        g = line[:, 1] / np.float32(255.0)
        b = line[:, 2] / np.float32(255.0)
        h, s, v = rgb_to_hsv_numba(r, g, b)
        key = h.astype(np.float32)
    elif criterion_id == 2:
        r = line[:, 0] / np.float32(255.0)
        g = line[:, 1] / np.float32(255.0)
        b = line[:, 2] / np.float32(255.0)
        h, s, v = rgb_to_hsv_numba(r, g, b)
        key = s.astype(np.float32)
    elif criterion_id == 3:
        max_vals = row_max(line)
        min_vals = row_min(line)
        key = (max_vals + min_vals) / np.float32(2.0)
    elif criterion_id == 4:
        key = row_min(line)
    else:
        for j in range(length):
            key[j] = (line[j, 0] + line[j, 1] + line[j, 2]) / np.float32(3.0)

    sorted_indices = np.argsort(key)
    sorted_line = line[sorted_indices].astype(np.uint8)
    return sorted_line

class PixelSortWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(Image.Image)
    error = pyqtSignal(str)

    def __init__(self, image, angle, criterion, intensity):
        super().__init__()
        self.image = image
        self.angle = angle
        self.criterion = criterion
        self.intensity = intensity

    def run(self):
        try:
            sorted_image = self.pixel_sort(self.image, self.angle, self.criterion, self.intensity)
            self.finished.emit(sorted_image)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{str(e)}\n{tb}")

    def pixel_sort(self, image, angle, criterion, intensity):
        # Convert image to NumPy array
        img_array = np.array(image)
        original_shape = img_array.shape

        # Rotate the image to align the sorting direction horizontally
        rotated_array = scipy.ndimage.rotate(
            img_array, -angle, reshape=True, order=0, mode='nearest'
        )

        height, width, channels = rotated_array.shape

        # Map criterion to integer id
        criterion_map = {
            'Brightness': 0,
            'Hue': 1,
            'Saturation': 2,
            'Intensity': 3,
            'Minimum': 4,
        }
        criterion_id = criterion_map.get(criterion, 0)

        sorted_array = rotated_array.copy()

        for i in range(height):
            line = sorted_array[i, :, :].copy()

            # Use Numba-compiled function to process the line
            sorted_line = process_line(line, criterion_id)

            # Apply sorting based on intensity
            if intensity < 1.0:
                # Randomly select pixels to replace based on intensity
                mask = np.random.rand(line.shape[0]) < intensity
                blended_line = line.copy()
                blended_line[mask] = sorted_line[mask]
                sorted_array[i, :, :] = blended_line
            else:
                sorted_array[i, :, :] = sorted_line

            # Update progress
            progress_percent = int(((i + 1) / height) * 100)
            self.progress.emit(progress_percent)

        # Rotate the sorted image back to original orientation
        sorted_array = scipy.ndimage.rotate(
            sorted_array, angle, reshape=True, order=0, mode='nearest'
        )

        # Crop or pad the image to match the original size
        sorted_array = self.crop_or_pad(sorted_array, original_shape)

        # Convert back to PIL Image
        sorted_image = Image.fromarray(sorted_array.astype(np.uint8))
        return sorted_image

    def crop_or_pad(self, img_array, target_shape):
        # Get current shape
        current_shape = img_array.shape
        pad_height = max(0, target_shape[0] - current_shape[0])
        pad_width = max(0, target_shape[1] - current_shape[1])

        # Pad the image if it's smaller than the target
        if pad_height > 0 or pad_width > 0:
            img_array = np.pad(
                img_array,
                ((0, pad_height), (0, pad_width), (0, 0)),
                mode='constant',
                constant_values=0
            )

        # Crop the image if it's larger than the target
        img_array = img_array[:target_shape[0], :target_shape[1], :]
        return img_array

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

        angle_slider = QSlider(Qt.Horizontal)
        angle_slider.setMinimum(0)
        angle_slider.setMaximum(359)
        angle_slider.setValue(0)
        angle_slider.setTickInterval(30)
        angle_slider.setTickPosition(QSlider.TicksBelow)
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

        intensity_slider = QSlider(Qt.Horizontal)
        intensity_slider.setMinimum(1)
        intensity_slider.setMaximum(100)
        intensity_slider.setValue(100)
        intensity_slider.setTickInterval(10)
        intensity_slider.setTickPosition(QSlider.TicksBelow)
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
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        original_container.addWidget(self.original_label)
        images_layout.addLayout(original_container)

        # Sorted Image
        sorted_container = QVBoxLayout()
        self.sorted_label = QLabel("Sorted Image")
        self.sorted_label.setAlignment(Qt.AlignCenter)
        self.sorted_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        self.intensity_value_label.setText(f"{value}%")

    def update_angle_label(self, value):
        self.angle_value_label.setText(f"{value}°")

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
    print("Starting application...")
    app = QApplication(sys.argv)
    print("QApplication created")
    window = PixelSortApp()
    print("Window created")
    window.show()
    print("Window shown")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
