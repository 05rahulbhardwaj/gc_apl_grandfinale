"""
CrowdPulse AI - People Counter
Uses YOLOv8n to count people in an RTSP camera stream.
Runs inference in a background thread with configurable interval.
"""

import time
import logging
import threading
from typing import Optional

import cv2
import numpy as np

from backend.config import (
    YOLO_INFERENCE_INTERVAL,
    YOLO_MODEL_NAME,
    YOLO_CONFIDENCE_THRESHOLD,
    PERSON_CLASS_ID,
)

logger = logging.getLogger(__name__)


class PeopleCounter:
    """Reads an RTSP stream and counts people using YOLOv8."""

    MAX_RETRIES = 10
    INITIAL_BACKOFF = 2.0   # seconds
    MAX_BACKOFF = 60.0      # seconds

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url

        # YOLO model (lazy-loaded on first start)
        self._model = None

        # Thread-safe state
        self._lock = threading.Lock()
        self._person_count: int = 0
        self._raw_frame: Optional[np.ndarray] = None
        self._annotated_frame: Optional[np.ndarray] = None
        self._last_inference_time: float = 0.0

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    # ── public API ────────────────────────────────────────────

    def start(self) -> None:
        """Start the background capture / inference thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("PeopleCounter already running")
            return

        self._load_model()
        self._running.set()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("PeopleCounter started for %s", self.rtsp_url)

    def stop(self) -> None:
        """Signal the thread to stop and wait for it."""
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("PeopleCounter stopped")

    def get_count(self) -> int:
        """Return the most recent person count (thread-safe)."""
        with self._lock:
            return self._person_count

    def get_annotated_frame(self) -> Optional[np.ndarray]:
        """Return the latest frame with YOLO bounding boxes."""
        with self._lock:
            if self._annotated_frame is not None:
                return self._annotated_frame.copy()
            return None

    def get_raw_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._raw_frame is not None:
                return self._raw_frame.copy()
            return None

    def set_rtsp_url(self, url: str) -> None:
        """Change the RTSP URL. Caller should stop/start around this."""
        self.rtsp_url = url

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    # ── private ───────────────────────────────────────────────

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO
            self._model = YOLO(YOLO_MODEL_NAME)
            logger.info("YOLOv8 model '%s' loaded", YOLO_MODEL_NAME)
        except Exception as exc:
            logger.error("Failed to load YOLO model: %s", exc)
            raise

    def _capture_loop(self) -> None:
        """Main loop: open stream → read frames → run YOLO → repeat."""
        backoff = self.INITIAL_BACKOFF
        retries = 0

        while self._running.is_set():
            cap = cv2.VideoCapture(self.rtsp_url)
            if not cap.isOpened():
                logger.warning(
                    "Cannot open RTSP stream '%s' (attempt %d/%d). "
                    "Retrying in %.1fs …",
                    self.rtsp_url, retries + 1, self.MAX_RETRIES, backoff,
                )
                retries += 1
                if retries > self.MAX_RETRIES:
                    logger.error("Max retries exceeded – PeopleCounter giving up")
                    self._running.clear()
                    break
                time.sleep(backoff)
                backoff = min(backoff * 2, self.MAX_BACKOFF)
                continue

            # Connected – reset backoff
            backoff = self.INITIAL_BACKOFF
            retries = 0
            logger.info("RTSP stream opened: %s", self.rtsp_url)

            while self._running.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Frame read failed – reconnecting …")
                    break

                with self._lock:
                    self._raw_frame = frame

                now = time.time()
                if now - self._last_inference_time >= YOLO_INFERENCE_INTERVAL:
                    self._run_inference(frame)
                    self._last_inference_time = now

                # Small sleep so we don't spin at 100 % CPU
                time.sleep(0.03)

            cap.release()

    def _run_inference(self, frame: np.ndarray) -> None:
        """Run YOLOv8 on a single frame and update counts."""
        if self._model is None:
            return

        try:
            results = self._model(
                frame,
                conf=YOLO_CONFIDENCE_THRESHOLD,
                classes=[PERSON_CLASS_ID],
                verbose=False,
            )
            result = results[0]

            count = 0
            annotated = frame.copy()

            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id != PERSON_CLASS_ID:
                    continue
                count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    annotated,
                    f"Person {conf:.0%}",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )

            # Draw total count overlay
            cv2.putText(
                annotated,
                f"People: {count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2,
            )

            with self._lock:
                self._person_count = count
                self._annotated_frame = annotated

        except Exception as exc:
            logger.error("YOLO inference error: %s", exc)
