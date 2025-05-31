import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
import numpy as np
from numba import njit
import scipy.ndimage
from .logger import get_logger

logger = get_logger('PixelSortWorker')

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
        self.logger = get_logger('PixelSortWorker')
        self.image = image
        self.angle = angle
        self.criterion = criterion
        self.intensity = intensity
        self.logger.info(f"Initialized worker with angle={angle}, criterion={criterion}, intensity={intensity}")

    def run(self):
        try:
            self.logger.info("Starting pixel sorting operation")
            sorted_image = self.pixel_sort(self.image, self.angle, self.criterion, self.intensity)
            self.logger.info("Pixel sorting completed successfully")
            self.finished.emit(sorted_image)
        except Exception as e:
            self.logger.error(f"Error during pixel sorting: {str(e)}", exc_info=True)
            tb = traceback.format_exc()
            self.error.emit(f"{str(e)}\n{tb}")

    def pixel_sort(self, image, angle, criterion, intensity):
        self.logger.debug(f"Starting pixel_sort with image size {image.size}")
        # Convert image to NumPy array
        img_array = np.array(image)
        original_shape = img_array.shape
        self.logger.debug(f"Original image shape: {original_shape}")

        # Rotate the image to align the sorting direction horizontally
        self.logger.debug(f"Rotating image by {-angle} degrees")
        rotated_array = scipy.ndimage.rotate(
            img_array, -angle, reshape=True, order=0, mode='nearest'
        )

        height, width, channels = rotated_array.shape
        self.logger.debug(f"Rotated image shape: {rotated_array.shape}")

        # Map criterion to integer id
        criterion_map = {
            'Brightness': 0,
            'Hue': 1,
            'Saturation': 2,
            'Intensity': 3,
            'Minimum': 4,
        }
        criterion_id = criterion_map.get(criterion, 0)
        self.logger.debug(f"Using criterion ID: {criterion_id} ({criterion})")

        sorted_array = rotated_array.copy()

        for i in range(height):
            line = sorted_array[i, :, :].copy()

            # Use Numba-compiled function to process the line
            sorted_line = process_line(line, criterion_id)

            # Apply sorting based on intensity
            if intensity < 1.0:
                self.logger.debug(f"Applying partial sorting with intensity {intensity}")
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
        self.logger.debug(f"Rotating image back by {angle} degrees")
        sorted_array = scipy.ndimage.rotate(
            sorted_array, angle, reshape=True, order=0, mode='nearest'
        )

        # Crop or pad the image to match the original size
        self.logger.debug("Cropping/padding image to match original size")
        sorted_array = self.crop_or_pad(sorted_array, original_shape)

        # Convert back to PIL Image
        sorted_image = Image.fromarray(sorted_array.astype(np.uint8))
        self.logger.debug("Pixel sorting completed")
        return sorted_image

    def crop_or_pad(self, img_array, target_shape):
        self.logger.debug(f"Crop/pad operation: current shape {img_array.shape} -> target shape {target_shape}")
        # Get current shape
        current_shape = img_array.shape
        pad_height = max(0, target_shape[0] - current_shape[0])
        pad_width = max(0, target_shape[1] - current_shape[1])

        # Pad the image if it's smaller than the target
        if pad_height > 0 or pad_width > 0:
            self.logger.debug(f"Padding image: height={pad_height}, width={pad_width}")
            img_array = np.pad(
                img_array,
                ((0, pad_height), (0, pad_width), (0, 0)),
                mode='constant',
                constant_values=0
            )

        # Crop the image if it's larger than the target
        img_array = img_array[:target_shape[0], :target_shape[1], :]
        return img_array 