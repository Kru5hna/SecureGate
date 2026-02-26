"""
Detection module for license plate detection and OCR.
Uses YOLO for plate detection and EasyOCR for text extraction.
"""

import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract

# Windows specific: Set tesseract path (Change this if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ─── Lazy-loaded globals ───────────────────────────────────────────
_yolo_model = None
_ocr_reader = None

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best (1).pt")

# Indian license plate format patterns
# Standard: XX00XX0000 or XX00X0000 (e.g., MH31AB1234, MH31A1234)
PLATE_PATTERNS = [
    re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$"),       # MH31AB1234
    re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}$"),      # Partial matches
    re.compile(r"^[A-Z]{2}\s?\d{2}\s?[A-Z]{1,3}\s?\d{4}$"),  # With spaces
]


def load_model():
    """Load the YOLO model (lazy loading)."""
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO(MODEL_PATH)
            print(f"[DETECTION] YOLO model loaded from: {MODEL_PATH}")
        except Exception as e:
            print(f"[DETECTION] Error loading model: {e}")
            raise e
    return _yolo_model


def load_ocr():
    """Load the EasyOCR reader (lazy loading)."""
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
        print("[DETECTION] EasyOCR reader initialized.")
    return _ocr_reader


def clean_plate_text(text):
    """
    Clean and normalize extracted plate text.
    Removes unwanted characters and standardizes format.
    """
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text)
    cleaned = cleaned.upper().strip()

    # Common OCR misreads
    replacements = {
        "O": "0",  # Only replace O with 0 in numeric positions
        "I": "1",
        "S": "5",
        "B": "8",
        "G": "6",
        "Z": "2",
    }

    # Apply smart replacements — only in expected digit positions
    if len(cleaned) >= 4:
        # First 2 chars should be letters (state code)
        state = cleaned[:2]
        rest = cleaned[2:]

        # Next 2 should be digits (district code)
        district = ""
        for ch in rest[:2]:
            if ch in replacements and not ch.isdigit():
                district += replacements[ch]
            else:
                district += ch
        rest = rest[2:]

        # Remaining: 1-3 letters + 1-4 digits
        cleaned = state + district + rest

    return cleaned


def validate_plate_format(plate_text):
    """
    Validate if the text matches Indian license plate format.
    Returns (is_valid, formatted_text)
    """
    cleaned = clean_plate_text(plate_text)

    for pattern in PLATE_PATTERNS:
        if pattern.match(cleaned):
            return True, cleaned

    # Even if format doesn't match perfectly, return the cleaned text
    # (OCR may not be perfect, but we still want to check the database)
    return False, cleaned


def preprocess_plate_image(plate_img):
    """
    Preprocess the cropped plate image for better OCR accuracy.
    Creates an array of different preprocessed versions to try OCR on.
    """
    variants = []
    
    # 1. Original BGR
    variants.append(plate_img)
    
    # 2. Grayscale
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    variants.append(gray)

    # Resize (scale up to improve OCR resolution)
    resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    variants.append(resized)

    # 3. Bilateral filter to reduce noise while keeping edges sharp
    blur = cv2.bilateralFilter(resized, 11, 17, 17)
    variants.append(blur)

    # 4. Otsu Thresholding
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(otsu)
    
    # 5. Adaptive Thresholding
    adaptive = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    variants.append(adaptive)

    # 6. Morphological Operations (Opening to remove noise, Closing to close small holes)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
    variants.append(morph)

    return variants


def detect_and_read(image_path):
    """
    Main detection pipeline:
    1. Run YOLO to detect license plates
    2. Crop detected regions
    3. Run OCR on each crop
    4. Validate and return results
    
    Returns a list of detection results.
    """
    model = load_model()
    reader = load_ocr()

    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        return {"error": f"Could not read image: {image_path}", "detections": []}

    img_h, img_w = img.shape[:2]

    # Run YOLO inference
    results = model.predict(source=image_path, conf=0.25, verbose=False)

    detections = []
    annotated_img = img.copy()

    for result in results:
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            continue

        for i, box in enumerate(boxes):
            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])

            # Ensure coordinates are within image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_w, x2)
            y2 = min(img_h, y2)

            # Crop the license plate region with a slightly larger padding
            pad = 10
            crop_y1 = max(0, y1 - pad)
            crop_y2 = min(img_h, y2 + pad)
            crop_x1 = max(0, x1 - pad)
            crop_x2 = min(img_w, x2 + pad)

            plate_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

            if plate_crop.size == 0:
                continue

            # Preprocess the plate image into multiple variants
            processed_variants = preprocess_plate_image(plate_crop)

            # Run OCR on multiple preprocessed versions and pick the best
            ocr_texts = []

            for processed_img in processed_variants:
                try:
                    # Provide an "allowlist" to force EasyOCR to only read uppercase letters and numbers
                    ocr_result = reader.readtext(
                        processed_img, 
                        detail=1,
                        allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                        paragraph=False,
                        mag_ratio=2.0  # Add internal magnification
                    )
                    
                    # Sometimes plate text is split into multiple bounding boxes by OCR
                    # Example: ["MH20", "EE0841"]
                    if len(ocr_result) > 1:
                        # Combine multiple detections vertically/horizontally
                        combined_text = "".join([det[1] for det in ocr_result])
                        avg_conf = sum([det[2] for det in ocr_result]) / len(ocr_result)
                        cleaned_combo = clean_plate_text(combined_text)
                        if len(cleaned_combo) >= 4 and len(cleaned_combo) <= 12:
                            ocr_texts.append((cleaned_combo, avg_conf))

                    # Also consider individual boxes
                    for detection in ocr_result:
                        text = detection[1]
                        ocr_conf = detection[2]
                        cleaned = clean_plate_text(text)
                        if len(cleaned) >= 4 and len(cleaned) <= 12:
                            ocr_texts.append((cleaned, ocr_conf))
                            
                except Exception as e:
                    print(f"[DETECTION] EasyOCR error: {e}")
                    pass

            # ─── FALLBACK: Tesseract OCR ───
            tesseract_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            for processed_img in processed_variants:
                 try:
                     text = pytesseract.image_to_string(processed_img, config=tesseract_config)
                     cleaned = clean_plate_text(text)
                     if len(cleaned) >= 4 and len(cleaned) <= 12:
                         # We assign a baseline confidence of 0.6 for Tesseract matches
                         ocr_texts.append((cleaned, 0.6))
                 except Exception as e:
                     # Silently fail if Tesseract is not installed
                     pass

            # Pick the best OCR result (longest valid text with highest confidence)
            best_text = ""
            best_conf = 0.0

            if ocr_texts:
                # Sort by: valid format first, then by confidence
                for text, ocr_conf in ocr_texts:
                    is_valid, formatted = validate_plate_format(text)
                    score = ocr_conf + (0.5 if is_valid else 0) + (len(text) * 0.01)
                    if score > best_conf or (score == best_conf and len(text) > len(best_text)):
                        best_text = formatted
                        best_conf = ocr_conf

            is_valid, final_text = validate_plate_format(best_text) if best_text else (False, "")

            # Save cropped plate image
            crop_filename = f"plate_crop_{i}_{os.path.basename(image_path)}"
            crop_path = os.path.join(os.path.dirname(image_path), crop_filename)
            cv2.imwrite(crop_path, plate_crop)

            # Draw bounding box on the annotated image
            color = (0, 255, 0)  # Green
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 3)
            label = f"{final_text} ({conf:.2f})"
            cv2.putText(
                annotated_img, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )

            detections.append({
                "bbox": [x1, y1, x2, y2],
                "detection_confidence": round(conf, 3),
                "plate_text": final_text,
                "ocr_confidence": round(best_conf, 3),
                "is_valid_format": is_valid,
                "crop_path": crop_filename,
            })

    # Save annotated image
    annotated_filename = f"annotated_{os.path.basename(image_path)}"
    annotated_path = os.path.join(os.path.dirname(image_path), annotated_filename)
    cv2.imwrite(annotated_path, annotated_img)

    return {
        "detections": detections,
        "annotated_image": annotated_filename,
        "total_plates_found": len(detections),
    }


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        print(f"Testing detection on: {test_image}")
        result = detect_and_read(test_image)
        print(f"Found {result['total_plates_found']} plate(s):")
        for d in result["detections"]:
            print(f"  Plate: {d['plate_text']} | Confidence: {d['ocr_confidence']:.2f} | Valid: {d['is_valid_format']}")
    else:
        print("Usage: python detection.py <image_path>")
