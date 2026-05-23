"""
CrowdPulse AI - Ticket Scanner
Uses the laptop webcam + OpenCV QRCodeDetector to scan QR-code tickets.
Parses JSON ticket data, detects duplicates, enforces cooldown between rescans.
"""

import json
import time
import logging
import threading
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from backend.config import TICKET_SCAN_INTERVAL
from backend.models import TicketData, TicketScanEvent
from backend.utils.stadium_config import STAND_GATE_ROUTING

logger = logging.getLogger(__name__)

SCAN_COOLDOWN_SECONDS = 3.0  # min interval between same-ticket rescans


class TicketScanner:
    """Scans QR-code tickets from a webcam feed."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._qr_detector = cv2.QRCodeDetector()

        # Thread-safe state
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._latest_scan: Optional[TicketScanEvent] = None
        self._scan_history: list[TicketScanEvent] = []

        # Duplicate / cooldown tracking: ticket_id → last scan timestamp
        self._last_scan_times: dict[str, float] = {}
        self._scanned_ids: set[str] = set()

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    # ── public API ────────────────────────────────────────────

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            logger.warning("TicketScanner already running")
            return

        self._running.set()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        logger.info("TicketScanner started (camera %d)", self.camera_index)

    def stop(self) -> None:
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("TicketScanner stopped")

    def get_latest_scan(self) -> Optional[TicketScanEvent]:
        with self._lock:
            return self._latest_scan

    def get_scan_history(self) -> list[TicketScanEvent]:
        with self._lock:
            return list(self._scan_history)

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._frame is not None:
                return self._frame.copy()
            return None

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @property
    def total_scans(self) -> int:
        with self._lock:
            return len(self._scan_history)

    # ── private ───────────────────────────────────────────────

    def _scan_loop(self) -> None:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            logger.error(
                "Cannot open webcam (index %d). TicketScanner will not run.",
                self.camera_index,
            )
            self._running.clear()
            return

        logger.info("Webcam opened (index %d)", self.camera_index)

        while self._running.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.warning("Webcam frame read failed")
                time.sleep(0.5)
                continue

            with self._lock:
                self._frame = frame

            # Attempt QR detection
            try:
                data, bbox, _ = self._qr_detector.detectAndDecode(frame)
            except Exception as exc:
                logger.debug("QR detection error: %s", exc)
                data = ""
                bbox = None

            if data:
                self._process_qr(data)

            time.sleep(TICKET_SCAN_INTERVAL)

        cap.release()

    def _process_qr(self, raw_data: str) -> None:
        """Parse a QR payload and create a TicketScanEvent."""
        now = time.time()

        try:
            payload = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            logger.debug("QR data is not valid JSON: %s", raw_data[:80])
            return

        # Extract fields (defensive)
        ticket_id = str(payload.get("id", "UNKNOWN"))
        gate = str(payload.get("gate", "Gate 1"))
        stand = str(payload.get("stand", "North Stand"))
        seat = str(payload.get("seat", "A-1"))
        name = str(payload.get("name", "Unknown"))

        # ── Cooldown check ────────────────────────────────────
        last_time = self._last_scan_times.get(ticket_id, 0)
        if now - last_time < SCAN_COOLDOWN_SECONDS:
            return  # silently ignore rapid rescans

        self._last_scan_times[ticket_id] = now

        # ── Duplicate check ───────────────────────────────────
        is_duplicate = ticket_id in self._scanned_ids
        self._scanned_ids.add(ticket_id)

        # ── Determine status ──────────────────────────────────
        status = "success"
        is_fake = False

        if is_duplicate:
            status = "duplicate"
        elif ticket_id.startswith("FAKE"):
            is_fake = True
            status = "invalid"
        else:
            # Check if fan is at the correct gate
            routing = STAND_GATE_ROUTING.get(stand, {})
            valid_gates = routing.get("primary_gates", []) + routing.get(
                "alternate_gates", []
            )
            if valid_gates and gate not in valid_gates:
                status = "wrong_gate"

        ticket = TicketData(
            ticket_id=ticket_id,
            fan_name=name,
            gate=gate,
            stand=stand,
            seat=seat,
            is_valid=not is_fake,
            scanned_at=datetime.now(),
        )

        event = TicketScanEvent(
            ticket=ticket,
            scan_time=datetime.now(),
            is_duplicate=is_duplicate,
            is_fake=is_fake,
            gate_scanned=gate,
            status=status,
        )

        with self._lock:
            self._latest_scan = event
            self._scan_history.append(event)

        log_fn = logger.warning if status != "success" else logger.info
        log_fn("Ticket scanned: %s → %s (%s)", ticket_id, gate, status)
