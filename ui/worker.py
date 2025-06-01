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

    def __init__(self, image, angle, criterion, pattern, intensity):
        super().__init__()
        self.logger = get_logger('PixelSortWorker')
        self.image = image
        self.angle = angle
        self.criterion = criterion
        self.pattern = pattern
        self.intensity = intensity
        self.logger.info(f"Initialized worker with angle={angle}, criterion={criterion}, pattern={pattern}, intensity={intensity}")

    def run(self):
        try:
            self.logger.info("Starting pixel sorting operation")
            sorted_image = self.pixel_sort(self.image, self.angle, self.criterion, self.pattern, self.intensity)
            self.logger.info("Pixel sorting completed successfully")
            self.finished.emit(sorted_image)
        except Exception as e:
            self.logger.error(f"Error during pixel sorting: {str(e)}", exc_info=True)
            tb = traceback.format_exc()
            self.error.emit(f"{str(e)}\n{tb}")

    def pixel_sort(self, image, angle, criterion, pattern, intensity):
        self.logger.debug(f"Starting pixel_sort with image size {image.size}")
        # Convert image to NumPy array
        img_array = np.array(image)
        height, width, channels = img_array.shape
        self.logger.debug(f"Original image shape: {img_array.shape}")

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
        self.logger.debug(f"Using pattern: {pattern}")

        # Convert angle to radians
        angle_rad = np.radians(angle)
        
        # Normalize angle to -180 to 180 degrees
        angle_rad = angle_rad % (2 * np.pi)
        if angle_rad > np.pi:
            angle_rad -= 2 * np.pi
            
        # Determine if we should shear horizontally or vertically
        # For angles between -45 and 45 degrees, shear horizontally
        # For angles between 45 and 135 degrees, shear vertically
        if -np.pi/4 <= angle_rad <= np.pi/4:
            # Shear horizontally
            shear_factor = np.tan(angle_rad)
            shear_matrix = np.array([
                [1, shear_factor, 0],
                [0, 1, 0],
                [0, 0, 1]
            ])
            inverse_shear_matrix = np.array([
                [1, -shear_factor, 0],
                [0, 1, 0],
                [0, 0, 1]
            ])
            # Sort horizontally
            sort_axis = 1
        else:
            # Shear vertically
            shear_factor = 1.0 / np.tan(angle_rad)
            shear_matrix = np.array([
                [1, 0, 0],
                [shear_factor, 1, 0],
                [0, 0, 1]
            ])
            inverse_shear_matrix = np.array([
                [1, 0, 0],
                [-shear_factor, 1, 0],
                [0, 0, 1]
            ])
            # Sort vertically
            sort_axis = 0
        
        # Apply shear transformation
        self.logger.debug("Applying shear transformation")
        sheared_array = scipy.ndimage.affine_transform(
            img_array,
            shear_matrix,
            offset=[0, 0, 0],
            order=1,
            mode='wrap',
            cval=0
        )

        # Sort pixels
        self.logger.debug("Sorting pixels")
        sorted_array = sheared_array.copy()
        
        # Process each line along the appropriate axis
        if sort_axis == 1:  # Sort horizontally
            for i in range(sheared_array.shape[0]):
                line = sorted_array[i, :, :].copy()
                sorted_line = process_line(line, criterion_id)
                if intensity < 1.0:
                    mask = np.random.rand(line.shape[0]) < intensity
                    blended_line = line.copy()
                    blended_line[mask] = sorted_line[mask]
                    sorted_array[i, :, :] = blended_line
                else:
                    sorted_array[i, :, :] = sorted_line
                progress_percent = int(((i + 1) / sheared_array.shape[0]) * 100)
                self.progress.emit(progress_percent)
        else:  # Sort vertically
            for i in range(sheared_array.shape[1]):
                line = sorted_array[:, i, :].copy()
                sorted_line = process_line(line, criterion_id)
                if intensity < 1.0:
                    mask = np.random.rand(line.shape[0]) < intensity
                    blended_line = line.copy()
                    blended_line[mask] = sorted_line[mask]
                    sorted_array[:, i, :] = blended_line
                else:
                    sorted_array[:, i, :] = sorted_line
                progress_percent = int(((i + 1) / sheared_array.shape[1]) * 100)
                self.progress.emit(progress_percent)

        # Apply inverse shear transformation
        self.logger.debug("Applying inverse shear transformation")
        result_array = scipy.ndimage.affine_transform(
            sorted_array,
            inverse_shear_matrix,
            offset=[0, 0, 0],
            order=1,
            mode='wrap',
            cval=0
        )

        # Ensure the result has the same shape as the input
        if result_array.shape != img_array.shape:
            result_array = self.maintain_aspect_ratio(result_array, img_array.shape)

        # Convert back to PIL Image
        sorted_image = Image.fromarray(result_array.astype(np.uint8))
        self.logger.debug("Pixel sorting completed")
        return sorted_image

    def get_line_points(self, x1, y1, x2, y2):
        """Get all points along a line using Bresenham's line algorithm."""
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        n = 1 + dx + dy
        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            points.append((x, y))
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return points

    def maintain_aspect_ratio(self, img_array, target_shape):
        """Maintain aspect ratio while resizing the image to match target shape."""
        self.logger.debug(f"Maintaining aspect ratio: current shape {img_array.shape} -> target shape {target_shape}")
        
        current_height, current_width = img_array.shape[:2]
        target_height, target_width = target_shape[:2]
        
        # Calculate scaling factors
        scale_h = target_height / current_height
        scale_w = target_width / current_width
        
        # Use the smaller scaling factor to maintain aspect ratio
        scale = min(scale_h, scale_w)
        
        # Calculate new dimensions
        new_height = int(current_height * scale)
        new_width = int(current_width * scale)
        
        # Resize the image
        resized = scipy.ndimage.zoom(
            img_array,
            (scale, scale, 1) if len(img_array.shape) == 3 else (scale, scale),
            order=1,
            mode='constant',
            cval=0
        )
        
        # Create a new array with target shape
        result = np.zeros(target_shape, dtype=img_array.dtype)
        
        # Calculate padding
        pad_h = (target_height - new_height) // 2
        pad_w = (target_width - new_width) // 2
        
        # Copy the resized image into the center of the result
        result[pad_h:pad_h + new_height, pad_w:pad_w + new_width] = resized
        
        return result 