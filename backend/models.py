"""
CrowdPulse AI - Pydantic Data Models
Defines all data structures used across the system.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────

class DensityLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    CONGESTION = "congestion"
    WEATHER = "weather"
    SECURITY = "security"
    MEDICAL = "medical"
    FIRE = "fire"
    SUSPICIOUS = "suspicious"
    VIP = "vip"
    STAMPEDE_RISK = "stampede_risk"


class ActionType(str, Enum):
    NOTIFY_FANS = "notify_fans"
    DISPATCH_STAFF = "dispatch_staff"
    OPEN_GATE = "open_gate"
    INCREASE_STAFF = "increase_staff"
    MAINTAIN_ACCESS = "maintain_access"
    EMERGENCY_PROTOCOL = "emergency_protocol"
    EXECUTE_ALL = "execute_all"


# ─── Zone & Gate Models ──────────────────────────────────────

class ZoneStatus(BaseModel):
    zone_id: str
    zone_name: str
    person_count: int = 0
    capacity: int = 1000
    density_level: DensityLevel = DensityLevel.LOW
    density_value: float = 0.0  # people per sq meter
    entry_rate: float = 0.0     # people per minute
    is_covered: bool = False
    last_updated: datetime = Field(default_factory=datetime.now)


class GateData(BaseModel):
    gate_id: str
    gate_name: str
    person_count: int = 0
    entry_rate: float = 0.0       # scans per minute
    avg_wait_time: float = 0.0    # minutes
    capacity_per_min: int = 120
    density_level: DensityLevel = DensityLevel.LOW
    is_open: bool = True
    assigned_stands: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


# ─── Ticket Models ───────────────────────────────────────────

class TicketData(BaseModel):
    ticket_id: str
    fan_name: str = "Unknown"
    gate: str = "Gate 1"
    stand: str = "North Stand"
    seat: str = "A-1"
    ticket_type: str = "general"  # general, vip, premium
    is_valid: bool = True
    scanned_at: Optional[datetime] = None


class TicketScanEvent(BaseModel):
    ticket: TicketData
    scan_time: datetime = Field(default_factory=datetime.now)
    is_duplicate: bool = False
    is_fake: bool = False
    gate_scanned: str = ""
    status: str = "success"  # success, duplicate, invalid, wrong_gate


# ─── Weather Models ──────────────────────────────────────────

class WeatherData(BaseModel):
    temperature: float = 28.0       # Celsius
    humidity: float = 65.0          # percentage
    wind_speed: float = 12.0        # km/h
    wind_direction: float = 180.0   # degrees
    rain_probability: float = 0.0   # 0-100
    weather_code: int = 0
    weather_description: str = "Clear"
    is_raining: bool = False
    forecast_rain_minutes: Optional[int] = None  # rain expected in X minutes
    last_updated: datetime = Field(default_factory=datetime.now)


# ─── Agent Response Models ───────────────────────────────────

class AgentResponse(BaseModel):
    agent_name: str
    agent_icon: str = "🤖"
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: str = ""
    details: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    recommendations: list[str] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)


class Alert(BaseModel):
    alert_id: str = ""
    alert_type: AlertType = AlertType.CONGESTION
    severity: RiskLevel = RiskLevel.MEDIUM
    title: str = ""
    description: str = ""
    zone: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    is_resolved: bool = False


# ─── Action Plan Models ─────────────────────────────────────

class ActionItem(BaseModel):
    action_id: int = 0
    action_type: ActionType = ActionType.NOTIFY_FANS
    description: str = ""
    priority: RiskLevel = RiskLevel.MEDIUM
    is_executed: bool = False
    executed_at: Optional[datetime] = None


class ActionPlan(BaseModel):
    overall_risk: RiskLevel = RiskLevel.LOW
    risk_reason: str = ""
    safety_score: int = 78  # 0-100
    actions: list[ActionItem] = Field(default_factory=list)
    fan_message: str = ""
    volunteer_message: str = ""
    security_message: str = ""
    expected_impact: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


# ─── System State ────────────────────────────────────────────

class StadiumState(BaseModel):
    """Complete snapshot of stadium state at a given moment."""
    match_info: dict = Field(default_factory=lambda: {
        "team1": "CSK",
        "team2": "MI",
        "venue": "Wankhede Stadium",
        "status": "Pre-Match",
        "start_time": "19:30",
    })
    zones: list[ZoneStatus] = Field(default_factory=list)
    gates: list[GateData] = Field(default_factory=list)
    weather: WeatherData = Field(default_factory=WeatherData)
    total_crowd_inside: int = 0
    total_crowd_outside: int = 0
    total_capacity: int = 33000
    ticket_scans_per_min: float = 0.0
    security_personnel: int = 320
    volunteers_deployed: int = 150
    agent_responses: list[AgentResponse] = Field(default_factory=list)
    action_plan: ActionPlan = Field(default_factory=ActionPlan)
    alerts: list[Alert] = Field(default_factory=list)
    live_updates: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


# Fix forward reference for Alert in AgentResponse
AgentResponse.model_rebuild()
