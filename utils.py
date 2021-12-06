import cv2
import numpy as np


def inflate_erode(mask, size=50):
    mask_copy = mask.copy()
    mask_copy = cv2.blur(mask_copy, (size, size))
    mask_copy[mask_copy > 0] = 255
    mask_copy = cv2.blur(mask_copy, (size, size))
    mask_copy[mask_copy < 255] = 0

    return mask_copy


def erode_inflate(mask, size=20):
    mask_copy = mask.copy()
    mask_copy = cv2.blur(mask_copy, (size, size))
    mask_copy[mask_copy < 255] = 0
    mask_copy = cv2.blur(mask_copy, (size, size))
    mask_copy[mask_copy > 0] = 255

    return mask_copy


def contour_mask(mask):
    _, cnt, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    new_mask = np.zeros(mask.shape)
    max_area = 0
    max_index = 0
    for idx, c in enumerate(cnt):
        area = cv2.contourArea(c)
        if area > max_area:
            max_area = area
            max_index = idx
    cv2.drawContours(new_mask, cnt, max_index, 255, cv2.FILLED)

    return new_mask


def color_bbox(img):
    """Makes a bbox around a white object"""
    # Filter out non-white
    upper = np.array([255, 255, 255])
    lower = upper - 30
    color_mask = cv2.inRange(img, lower, upper)

    # Filter out little bits of white
    color_mask = inflate_erode(color_mask)
    color_mask = erode_inflate(color_mask)

    # Only use largest contour
    color_mask = contour_mask(color_mask)

    # Calculate bbox
    x, y, w, h = cv2.boundingRect(color_mask)
    height, width = color_mask.shape
    cx, cy = [
        int((start + side_length / 2) / max_length)
        for start, side_length, max_length in [
            (x, w, width),
            (y, h, height),
        ]
    ]

    # Create bbox mask
    bbox_mask = np.zeros([height, width, 1], dtype=np.float32)
    bbox_mask[y : y + h, x : x + w] = 1.0

    return bbox_mask, cx, cy
