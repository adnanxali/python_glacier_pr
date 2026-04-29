from ultralytics import YOLO
import cv2
import numpy as np
import joblib
from config import Config

model = YOLO(Config.YOLO_MODEL_PATH)
hybrid_model = joblib.load(Config.HYBRID_MODEL_PATH)

def get_detection_overlay(image_path):
    results = model.predict(source=image_path, save=True)
    image = cv2.imread(image_path)
    overlay = image.copy()

    for r in results:
        for c in r:
            contour = c.masks.xy.pop().astype(np.int32).reshape(-1, 1, 2)
            cv2.drawContours(overlay, [contour], -1, (0, 255, 0), thickness=cv2.FILLED)

    return overlay

def get_binary_mask(image_path):
    results = model.predict(source=image_path, save=True)
    img = cv2.imread(image_path)
    binary_mask = np.zeros(img.shape[:2], dtype=np.uint8)

    for r in results:
        for c in r:
            contour = c.masks.xy.pop().astype(np.int32).reshape(-1, 1, 2)
            cv2.drawContours(binary_mask, [contour], -1, 255, thickness=cv2.FILLED)

    return binary_mask

def extract_features_for_prediction(image_path1, image_path2):
    mask1 = get_binary_mask(image_path1)
    mask2 = get_binary_mask(image_path2)
    
    if mask1.shape != mask2.shape:
        mask2 = cv2.resize(mask2, (mask1.shape[1], mask1.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    area1 = np.sum(mask1 == 255)
    area2 = np.sum(mask2 == 255)
    intersection = np.sum(cv2.bitwise_and(mask1, mask2) == 255)
    union = np.sum(cv2.bitwise_or(mask1, mask2) == 255)
    
    if area1 == 0:
        return None
    
    growth_percentage = ((area2 - area1) / area1) * 100
    area_ratio = area2 / area1 if area1 > 0 else 0
    overlap_ratio = intersection / area1 if area1 > 0 else 0
    iou = intersection / union if union > 0 else 0
    
    contours1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    perimeter1 = sum([cv2.arcLength(c, True) for c in contours1])
    perimeter2 = sum([cv2.arcLength(c, True) for c in contours2])
    
    compactness1 = (4 * np.pi * area1) / (perimeter1 ** 2) if perimeter1 > 0 else 0
    compactness2 = (4 * np.pi * area2) / (perimeter2 ** 2) if perimeter2 > 0 else 0
    
    features = [
        area1,
        area2,
        growth_percentage,
        area_ratio,
        overlap_ratio,
        iou,
        perimeter1,
        perimeter2,
        compactness1,
        compactness2
    ]
    
    return features

def calculate_growth_and_overlay(image_path1, image_path2):
    mask1 = get_binary_mask(image_path1)
    mask2 = get_binary_mask(image_path2)

    if mask1.shape != mask2.shape:
        mask2 = cv2.resize(mask2, (mask1.shape[1], mask1.shape[0]), interpolation=cv2.INTER_NEAREST)

    image1 = cv2.imread(image_path1)
    image2 = cv2.imread(image_path2)

    intersection_mask = cv2.bitwise_and(mask1, mask2)
    growth_mask = cv2.bitwise_and(mask2, cv2.bitwise_not(mask1))

    intersection_color = (0, 255, 0)
    growth_color = (0, 0, 255)

    image2_with_intersection = overlay_mask_on_image(image2, intersection_mask, intersection_color, alpha=0.5)
    image2_with_growth = overlay_mask_on_image(image2_with_intersection, growth_mask, growth_color, alpha=0.5)

    total_area_mask1 = np.sum(mask1 == 255)
    total_area_mask2 = np.sum(mask2 == 255)
    intersection_area = np.sum(intersection_mask == 255)
    net_growth_area = total_area_mask2 - total_area_mask1

    growth_area = np.sum(growth_mask == 255)

    if total_area_mask1 > 0:
        growth_percentage = (net_growth_area / total_area_mask1) * 100
    else:
        growth_percentage = 0

    growth_status = "Increasing" if net_growth_area > 0 else "Decreasing"
    
    features = extract_features_for_prediction(image_path1, image_path2)
    if features is not None:
        features_array = np.array(features).reshape(1, -1)
        risk_prediction = hybrid_model.predict(features_array)[0]
        risk_binary = "Risky" if risk_prediction == 1 else "Not Risky"
    else:
        risk_binary = "Not Risky"
    
    if growth_percentage <= Config.LOW_RISK_THRESHOLD:
        risk_level = "Low Risk"
    elif growth_percentage <= Config.MEDIUM_RISK_THRESHOLD:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    return image2_with_growth, total_area_mask1, total_area_mask2, intersection_area, growth_area, growth_percentage, growth_status, risk_binary, risk_level

def overlay_mask_on_image(image, mask, color, alpha=0.5):
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    colored_mask = np.zeros_like(image)
    colored_mask[mask == 255] = color
    
    return cv2.addWeighted(colored_mask, alpha, image, 1 - alpha, 0)