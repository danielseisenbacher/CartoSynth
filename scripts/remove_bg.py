import cv2
import numpy as np
import os

base_dir = "tiff_fonts"
for directory in os.listdir(base_dir):
    images = os.listdir(os.path.join(base_dir, directory))
    for img_name in images:
        if img_name.startswith("bgrmv_"):
            continue

        image_path = os.path.join(base_dir, directory, img_name)
        image_path_new = os.path.join(base_dir, directory, f"bgrmv_{img_name}")

        # Read image at higher resolution if possible
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

        # 2. Gentle blur to smooth edges BEFORE thresholding
        blurred = cv2.GaussianBlur(denoised, (3, 3), 0)

        # 3. Threshold
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 4. Light morphological operations
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        # 5. SMOOTH THE EDGES - Apply slight Gaussian blur to alpha channel
        binary_float = binary.astype(np.float32) / 255.0
        smoothed = cv2.GaussianBlur(binary_float, (3, 3), 0)
        alpha = (smoothed * 255).astype(np.uint8)

        # 6. Convert to RGBA with smoothed alpha
        rgba = np.zeros((alpha.shape[0], alpha.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = 0  # Black text
        rgba[:, :, 3] = alpha  # Smoothed alpha channel

        cv2.imwrite(image_path_new, rgba)