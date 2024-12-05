import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple


def find_red_hue_ranges(hue_channel: np.ndarray) -> Tuple[int, int, int, int]:
    """
    Find red hue ranges based on histogram peaks.

    Args:
        hue_channel (np.ndarray): Hue channel of the HSV image.

    Returns:
        Tuple[int, int, int, int]: (lower_red_hue1, upper_red_hue1, lower_red_hue2, upper_red_hue2)
    """
    # Compute histogram for hue channel
    hist = cv2.calcHist([hue_channel], [0], None, [180], [0, 180]).flatten()

    # Smooth the histogram to reduce noise
    hist_smooth = cv2.GaussianBlur(hist, (9, 9), 0)

    # Find peaks in the histogram
    peaks = []
    threshold = np.max(hist_smooth) * 0.1  # 10% of max value as threshold
    for i in range(1, len(hist_smooth) - 1):
        if (
            hist_smooth[i] > hist_smooth[i - 1]
            and hist_smooth[i] > hist_smooth[i + 1]
            and hist_smooth[i] > threshold
        ):
            peaks.append(i)

    # Assuming red has two peaks near 0 and 180
    lower_red_hue1 = max(peaks[0] - 10, 0) if len(peaks) > 0 else 0
    upper_red_hue1 = min(peaks[0] * 2 // 3, 180) if len(peaks) > 0 else 10

    lower_red_hue2 = max(peaks[1] - 10, 170) if len(peaks) > 1 else 170
    upper_red_hue2 = 180

    return lower_red_hue1, upper_red_hue1, lower_red_hue2, upper_red_hue2


def get_skin_mask(ycrcb_image: np.ndarray) -> np.ndarray:
    """
    Extract skin mask using YCrCb color space.

    Args:
        ycrcb_image (np.ndarray): Image in YCrCb color space.

    Returns:
        np.ndarray: Binary skin mask.
    """
    # Define skin color range in YCrCb
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    skin_mask = cv2.inRange(ycrcb_image, lower, upper)

    # Apply morphological operations to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel, iterations=2)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_DILATE, kernel, iterations=1)

    return skin_mask


def detect_acne(image: Image.Image, bbox: List[int]) -> Tuple[Image.Image, int]:
    """
    Detect acne regions in an image based on red color detection.

    Args:
        image (Image.Image): Input image.

    Returns:
        Image.Image: Image with detected acne regions highlighted.
    """
    # Internal Detection Parameters
    MIN_AREA: int = 30
    MAX_AREA: int = 7000
    CIRCULARITY_THRESH: float = 0.1
    BORDER_RED_DIFF_THRESH: int = 0  # Adjust as needed
    AVERAGE_RED_THRESHOLD_OFFSET: int = 0  # Adjust as needed

    # Convert PIL Image to OpenCV BGR format
    raw_image_cv: np.ndarray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    x1, y1, x2, y2 = bbox
    image_cv = raw_image_cv[y1:y2, x1:x2]

    # Convert to YCrCb and extract skin mask
    ycrcb_image: np.ndarray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2YCrCb)
    skin_mask: np.ndarray = get_skin_mask(ycrcb_image)

    # Extract red channel
    r_channel: np.ndarray = image_cv[:, :, 2]
    skin_r_values: np.ndarray = r_channel[skin_mask > 0]

    # If no skin regions detected, return original image
    if len(skin_r_values) == 0:
        return image, 100

    # Find average red threshold
    num_values: int = 5
    if len(skin_r_values) < num_values:
        num_values = len(skin_r_values)

    sorted_r: np.ndarray = np.sort(skin_r_values)
    min_red_values: np.ndarray = sorted_r[:num_values]
    max_red_values: np.ndarray = sorted_r[-num_values:]

    avg_min_red: float = float(np.mean(min_red_values)) if num_values > 0 else 0.0
    avg_max_red: float = float(np.mean(max_red_values)) if num_values > 0 else 0.0
    average_red_threshold: float = (
        avg_min_red + avg_max_red
    ) / 2.0 + AVERAGE_RED_THRESHOLD_OFFSET

    # Convert to HSV and extract hue channel
    blurred_initial: np.ndarray = cv2.GaussianBlur(image_cv, (5, 5), 0)
    hsv_initial: np.ndarray = cv2.cvtColor(blurred_initial, cv2.COLOR_BGR2HSV)
    hue_channel: np.ndarray = hsv_initial[:, :, 0]

    # Automatically find red hue ranges
    lower_red_hue1, upper_red_hue1, lower_red_hue2, upper_red_hue2 = (
        find_red_hue_ranges(hue_channel)
    )

    # Define red ranges in HSV
    lower_red1: np.ndarray = np.array([lower_red_hue1, 70, 50])
    upper_red1: np.ndarray = np.array([upper_red_hue1, 255, 255])
    lower_red2: np.ndarray = np.array([lower_red_hue2, 70, 50])
    upper_red2: np.ndarray = np.array([upper_red_hue2, 255, 255])

    # Create red masks
    red_mask1: np.ndarray = cv2.inRange(hsv_initial, lower_red1, upper_red1)
    red_mask2: np.ndarray = cv2.inRange(hsv_initial, lower_red2, upper_red2)
    red_mask: np.ndarray = cv2.bitwise_or(red_mask1, red_mask2)

    # Noise removal and smoothing
    kernel: np.ndarray = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    acne_mask: np.ndarray = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    acne_mask = cv2.morphologyEx(acne_mask, cv2.MORPH_CLOSE, kernel)
    acne_mask = cv2.GaussianBlur(acne_mask, (5, 5), 0)

    # Find contours
    contours, _ = cv2.findContours(
        acne_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter contours based on parameters
    filtered_contours: list = []
    for cnt in contours:
        area: float = cv2.contourArea(cnt)
        if not (MIN_AREA < area < MAX_AREA):
            continue

        perimeter: float = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        circularity: float = 4 * np.pi * (area / (perimeter * perimeter))
        if circularity < CIRCULARITY_THRESH:
            continue

        # Create mask for contour
        contour_mask: np.ndarray = np.zeros(acne_mask.shape, dtype=np.uint8)
        cv2.drawContours(contour_mask, [cnt], -1, 255, -1)  # type: ignore

        # Extract border mask
        border_mask: np.ndarray = cv2.subtract(
            contour_mask, cv2.erode(contour_mask, kernel, iterations=1)
        )

        # Calculate average red value on border
        border_mean_red: float = float(cv2.mean(r_channel, mask=border_mask)[0])

        # Compare with average red threshold
        if border_mean_red > average_red_threshold + BORDER_RED_DIFF_THRESH:
            filtered_contours.append(cnt)

    # Draw filtered contours on the result image
    result_image: np.ndarray = image_cv.copy()
    cv2.drawContours(result_image, filtered_contours, -1, (0, 255, 0), 2)

    # Convert OpenCV image back to PIL Image
    result_image_rgb: np.ndarray = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
    result_pil: Image.Image = Image.fromarray(result_image_rgb)

    total_area: float = image_cv.shape[0] * image_cv.shape[1]
    ance_percentage: float = (
        sum([cv2.contourArea(cnt) for cnt in filtered_contours]) / total_area * 100
    )
    score: int = 100 - min(50, int(ance_percentage * 20))

    return result_pil, score
