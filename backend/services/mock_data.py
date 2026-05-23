"""
CrowdPulse AI - Mock Data Generator
Simulates realistic crowd, gate, and ticket-scan data that advances through
the DEMO_SCENARIO phases defined in stadium_config.
"""

import random
import string
import threading
import logging
from datetime import datetime
from typing import Optional

from backend.models import (
    ZoneStatus,
    GateData,
    TicketData,
    TicketScanEvent,
    DensityLevel,
)
from backend.utils.stadium_config import (
    STADIUM_ZONES,
    STAND_GATE_ROUTING,
    DEMO_SCENARIO,
)
from backend.config import GATE_CAPACITIES, DENSITY_THRESHOLDS

logger = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikas", "Ananya", "Rohan", "Kavita",
    "Sanjay", "Meera", "Arjun", "Divya", "Raj", "Neha", "Karan", "Pooja",
    "Suresh", "Lakshmi", "Varun", "Nisha", "Aditya", "Ritu", "Mohit", "Swati",
]
LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Das", "Mehta",
    "Joshi", "Iyer", "Chopra", "Verma", "Nair", "Pillai", "Rao", "Bhatia",
]

STANDS = ["North Stand", "East Stand", "West Stand", "South Stand"]
GATES = ["Gate 1", "Gate 2", "Gate 3", "Gate 4", "Gate 5"]
TICKET_TYPES = ["general", "general", "general", "premium", "vip"]


def _jitter(value: int, pct: float = 0.08) -> int:
    """Add ±pct random noise to an integer value."""
    noise = random.uniform(-pct, pct)
    return max(0, int(value * (1 + noise)))


def _density_level_from_value(density: float) -> DensityLevel:
    if density <= DENSITY_THRESHOLDS["very_low"]:
        return DensityLevel.VERY_LOW
    elif density <= DENSITY_THRESHOLDS["low"]:
        return DensityLevel.LOW
    elif density <= DENSITY_THRESHOLDS["medium"]:
        return DensityLevel.MEDIUM
    elif density <= DENSITY_THRESHOLDS["high"]:
        return DensityLevel.HIGH
    return DensityLevel.VERY_HIGH


class MockDataGenerator:
    """Generates simulated crowd data that follows the demo scenario."""

    def __init__(self):
        self._phases = DEMO_SCENARIO["phases"]
        self._current_phase_idx: int = 0
        self._ticket_counter: int = 0
        self._lock = threading.Lock()
        self._scanned_ids: set[str] = set()
        logger.info(
            "MockDataGenerator initialised – %d phases available",
            len(self._phases),
        )

    # ── phase management ──────────────────────────────────────

    @property
    def current_phase(self) -> dict:
        with self._lock:
            return self._phases[self._current_phase_idx]

    @property
    def current_phase_index(self) -> int:
        with self._lock:
            return self._current_phase_idx

    @property
    def total_phases(self) -> int:
        return len(self._phases)

    def advance_phase(self) -> dict:
        """Move to the next phase; wraps around at the end."""
        with self._lock:
            self._current_phase_idx = (self._current_phase_idx + 1) % len(self._phases)
            phase = self._phases[self._current_phase_idx]
        logger.info("Advanced to phase %d: %s", phase["phase"], phase["description"])
        return phase

    def reset_phase(self) -> dict:
        """Reset to phase 1."""
        with self._lock:
            self._current_phase_idx = 0
            self._scanned_ids.clear()
            self._ticket_counter = 0
        return self._phases[0]

    # ── zone statuses ─────────────────────────────────────────

    def get_zone_statuses(self) -> list[ZoneStatus]:
        """Generate zone statuses based on the current demo phase."""
        phase = self.current_phase
        gate_crowds: dict[str, int] = phase.get("gate_crowds", {})

        zones: list[ZoneStatus] = []
        for zone_cfg in STADIUM_ZONES:
            zone_id = zone_cfg["zone_id"]
            zone_name = zone_cfg["zone_name"]
            capacity = zone_cfg["capacity"]
            area = zone_cfg["area_sqm"]
            is_covered = zone_cfg["is_covered"]

            # Determine person count
            if zone_name in gate_crowds:
                person_count = _jitter(gate_crowds[zone_name])
            elif zone_cfg["type"] == "stand":
                # Stands fill proportionally to the total gate traffic
                total_gate = sum(gate_crowds.values())
                ratio = random.uniform(0.3, 0.5)
                person_count = _jitter(int(total_gate * ratio / len(STANDS)))
            elif zone_cfg["type"] == "amenity":
                person_count = _jitter(int(capacity * random.uniform(0.1, 0.4)))
            elif zone_cfg["type"] == "entrance":
                person_count = _jitter(int(sum(gate_crowds.values()) * 0.15))
            else:
                person_count = _jitter(int(capacity * 0.2))

            person_count = min(person_count, capacity)
            density_value = round(person_count / max(area, 1), 2)
            entry_rate = round(random.uniform(5, 40), 1)

            zones.append(
                ZoneStatus(
                    zone_id=zone_id,
                    zone_name=zone_name,
                    person_count=person_count,
                    capacity=capacity,
                    density_level=_density_level_from_value(density_value),
                    density_value=density_value,
                    entry_rate=entry_rate,
                    is_covered=is_covered,
                    last_updated=datetime.now(),
                )
            )
        return zones

    # ── gate data ─────────────────────────────────────────────

    def get_gate_data(self) -> list[GateData]:
        """Generate gate-level data from the current phase."""
        phase = self.current_phase
        gate_crowds: dict[str, int] = phase.get("gate_crowds", {})
        gates: list[GateData] = []

        for gate_name in GATES:
            person_count = _jitter(gate_crowds.get(gate_name, 100))
            cap_per_min = GATE_CAPACITIES.get(gate_name, 120)

            # Calculate derived metrics
            entry_rate = round(random.uniform(20, cap_per_min * 0.9), 1)
            utilisation = person_count / max(cap_per_min * 5, 1)  # rough queue proxy
            avg_wait = round(max(0, utilisation * random.uniform(2, 8)), 1)

            # Density based on person count relative to a notional gate area (~400 sqm)
            density_val = person_count / 400.0
            density_level = _density_level_from_value(density_val)

            # Find assigned stands for this gate
            assigned_stands = []
            for zone_cfg in STADIUM_ZONES:
                if zone_cfg["zone_name"] == gate_name:
                    assigned_stands = zone_cfg.get("assigned_stands", [])
                    break

            gates.append(
                GateData(
                    gate_id=gate_name.lower().replace(" ", "_"),
                    gate_name=gate_name,
                    person_count=person_count,
                    entry_rate=entry_rate,
                    avg_wait_time=avg_wait,
                    capacity_per_min=cap_per_min,
                    density_level=density_level,
                    is_open=True,
                    assigned_stands=assigned_stands,
                    last_updated=datetime.now(),
                )
            )
        return gates

    # ── ticket scan events ────────────────────────────────────

    def get_random_ticket_scan(self) -> TicketScanEvent:
        """Generate a single random ticket-scan event."""
        with self._lock:
            self._ticket_counter += 1
            ticket_id = f"T{self._ticket_counter:04d}"

        gate = random.choice(GATES)
        stand = random.choice(STANDS)
        seat_letter = random.choice("ABCDEFGH")
        seat_num = random.randint(1, 60)
        seat = f"{seat_letter}-{seat_num}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        ticket_type = random.choice(TICKET_TYPES)

        # Occasional duplicates / fakes for demo realism
        is_duplicate = False
        is_fake = False
        status = "success"

        roll = random.random()
        if roll < 0.03:
            # Simulate a duplicate scan
            is_duplicate = True
            status = "duplicate"
            # Re-use an existing ID if we have any
            with self._lock:
                if self._scanned_ids:
                    ticket_id = random.choice(list(self._scanned_ids))
        elif roll < 0.05:
            is_fake = True
            status = "invalid"
            ticket_id = "FAKE-" + "".join(random.choices(string.ascii_uppercase, k=4))

        with self._lock:
            self._scanned_ids.add(ticket_id)

        # Check wrong-gate scenario
        routing = STAND_GATE_ROUTING.get(stand, {})
        valid_gates = routing.get("primary_gates", []) + routing.get("alternate_gates", [])
        if valid_gates and gate not in valid_gates and not is_fake:
            if random.random() < 0.15:
                status = "wrong_gate"

        ticket = TicketData(
            ticket_id=ticket_id,
            fan_name=name,
            gate=gate,
            stand=stand,
            seat=seat,
            ticket_type=ticket_type,
            is_valid=not is_fake,
            scanned_at=datetime.now(),
        )

        return TicketScanEvent(
            ticket=ticket,
            scan_time=datetime.now(),
            is_duplicate=is_duplicate,
            is_fake=is_fake,
            gate_scanned=gate,
            status=status,
        )

    # ── bulk helpers ──────────────────────────────────────────

    def get_ticket_scan_batch(self, count: int = 5) -> list[TicketScanEvent]:
        """Generate a small batch of ticket scans."""
        return [self.get_random_ticket_scan() for _ in range(count)]

    def get_phase_description(self) -> str:
        phase = self.current_phase
        return (
            f"Phase {phase['phase']} ({phase['time_label']}): "
            f"{phase['description']}"
        )
