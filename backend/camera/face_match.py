"""
Eternal Crowd Sense AI — Celebrity Face Match (Easter Egg)
Uses OpenCV face detection + histogram comparison.
"""

import os
import cv2
import numpy as np
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CELEB_DIR = _PROJECT_ROOT / "celebrity_image"

# Celebrity name mapping from filenames
CELEB_NAMES = {
    "1332971-bumbra.jpg": "Jasprit Bumrah",
    "7feabb3ef96be295573840ccb567f34b.jpg": "MS Dhoni",
    "Prime_Minister_Of_Bharat_Shri_Narendra_Damodardas_Modi_with_Shri_Rohit_Gurunath_Sharma_(Cropped).jpg": "Rohit Sharma",
    "Screenshot 2026-05-23 143745.jpg": "Sundar Pichai",
    "royal-challengers-bengaluru-s-virat-kohli-jpg.jpg": "Virat Kohli",
}

# Load Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def _detect_face(img):
    """Detect largest face in an image, return cropped face region."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    
    if len(faces) == 0:
        # If no face detected, use center crop as fallback
        h, w = img.shape[:2]
        size = min(h, w) // 2
        cx, cy = w // 2, h // 2
        return img[cy - size // 2:cy + size // 2, cx - size // 2:cx + size // 2]
    
    # Take the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    
    # Add some padding
    pad = int(0.2 * w)
    ih, iw = img.shape[:2]
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(iw, x + w + pad)
    y2 = min(ih, y + h + pad)
    
    return img[y1:y2, x1:x2]


def _face_histogram(face_img):
    """Compute a normalized color histogram for a face region."""
    face_resized = cv2.resize(face_img, (128, 128))
    hsv = cv2.cvtColor(face_resized, cv2.COLOR_BGR2HSV)
    
    # Compute histogram on H and S channels
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist


def _load_celebrity_data():
    """Load all celebrity images and precompute their face histograms."""
    celebs = []
    
    if not CELEB_DIR.exists():
        logger.warning("Celebrity image directory not found: %s", CELEB_DIR)
        return celebs
    
    for filename in os.listdir(CELEB_DIR):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        
        filepath = CELEB_DIR / filename
        img = cv2.imread(str(filepath))
        if img is None:
            continue
        
        face = _detect_face(img)
        if face is None or face.size == 0:
            continue
        
        hist = _face_histogram(face)
        name = CELEB_NAMES.get(filename, filename.split('.')[0].replace('_', ' ').title())
        
        # Create a small thumbnail for the response
        thumb = cv2.resize(img, (150, 150))
        _, thumb_buf = cv2.imencode('.jpg', thumb)
        thumb_b64 = base64.b64encode(thumb_buf).decode('utf-8')
        
        celebs.append({
            "name": name,
            "filename": filename,
            "histogram": hist,
            "thumbnail_b64": thumb_b64,
        })
    
    logger.info("Loaded %d celebrity faces from %s", len(celebs), CELEB_DIR)
    return celebs


# Preload celebrity data at import time
_CELEB_DATA = _load_celebrity_data()


def match_face(image_data: bytes) -> dict:
    """
    Compare a user's face (from webcam) against celebrity faces.
    Returns match results sorted by similarity.
    """
    # Decode the uploaded image
    nparr = np.frombuffer(image_data, np.uint8)
    user_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if user_img is None:
        return {"error": "Could not decode image"}
    
    # Detect and extract user's face
    user_face = _detect_face(user_img)
    if user_face is None or user_face.size == 0:
        return {"error": "No face detected in image"}
    
    user_hist = _face_histogram(user_face)
    
    # Compare against all celebrities
    results = []
    for celeb in _CELEB_DATA:
        # Use correlation method (higher = more similar, range 0 to 1)
        score = cv2.compareHist(user_hist, celeb["histogram"], cv2.HISTCMP_CORREL)
        # Normalize to percentage (0-100)
        similarity = max(0, min(100, int(score * 100)))
        
        results.append({
            "name": celeb["name"],
            "similarity": similarity,
            "thumbnail": f"data:image/jpeg;base64,{celeb['thumbnail_b64']}",
        })
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Create annotated user image with face rectangle
    gray = cv2.cvtColor(user_img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    for (x, y, w, h) in faces:
        cv2.rectangle(user_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    _, user_buf = cv2.imencode('.jpg', user_img)
    user_b64 = base64.b64encode(user_buf).decode('utf-8')
    
    return {
        "user_image": f"data:image/jpeg;base64,{user_b64}",
        "matches": results,
        "best_match": results[0] if results else None,
    }
