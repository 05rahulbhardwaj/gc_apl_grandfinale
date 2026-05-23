"""
CrowdPulse AI - Stadium Configuration
Defines the physical layout of the cricket stadium: zones, gates, stands, and their properties.
"""

# ─── Stadium Zones ────────────────────────────────────────────
# Each zone has: id, name, capacity, area (sq meters), position (for SVG), is_covered

STADIUM_ZONES = [
    {
        "zone_id": "gate_1",
        "zone_name": "Gate 1",
        "capacity": 800,
        "area_sqm": 400,
        "position": {"x": 20, "y": 50},   # percentage position on SVG
        "is_covered": False,
        "type": "gate",
        "assigned_stands": ["West Stand", "South Stand"],
    },
    {
        "zone_id": "gate_2",
        "zone_name": "Gate 2",
        "capacity": 1000,
        "area_sqm": 500,
        "position": {"x": 15, "y": 30},
        "is_covered": False,
        "type": "gate",
        "assigned_stands": ["East Stand", "North Stand"],
    },
    {
        "zone_id": "gate_3",
        "zone_name": "Gate 3",
        "capacity": 800,
        "area_sqm": 400,
        "position": {"x": 35, "y": 10},
        "is_covered": True,
        "type": "gate",
        "assigned_stands": ["North Stand"],
    },
    {
        "zone_id": "gate_4",
        "zone_name": "Gate 4",
        "capacity": 700,
        "area_sqm": 350,
        "position": {"x": 65, "y": 10},
        "is_covered": True,
        "type": "gate",
        "assigned_stands": ["North Stand", "East Stand"],
    },
    {
        "zone_id": "gate_5",
        "zone_name": "Gate 5",
        "capacity": 700,
        "area_sqm": 350,
        "position": {"x": 80, "y": 50},
        "is_covered": False,
        "type": "gate",
        "assigned_stands": ["East Stand", "South Stand"],
    },
    {
        "zone_id": "north_stand",
        "zone_name": "North Stand",
        "capacity": 8000,
        "area_sqm": 4000,
        "position": {"x": 50, "y": 8},
        "is_covered": True,
        "type": "stand",
        "assigned_stands": [],
    },
    {
        "zone_id": "south_stand",
        "zone_name": "South Stand",
        "capacity": 8000,
        "area_sqm": 4000,
        "position": {"x": 50, "y": 92},
        "is_covered": True,
        "type": "stand",
        "assigned_stands": [],
    },
    {
        "zone_id": "east_stand",
        "zone_name": "East Stand",
        "capacity": 9000,
        "area_sqm": 4500,
        "position": {"x": 85, "y": 50},
        "is_covered": True,
        "type": "stand",
        "assigned_stands": [],
    },
    {
        "zone_id": "west_stand",
        "zone_name": "West Stand",
        "capacity": 8000,
        "area_sqm": 4000,
        "position": {"x": 15, "y": 50},
        "is_covered": True,
        "type": "stand",
        "assigned_stands": [],
    },
    {
        "zone_id": "food_court",
        "zone_name": "Food Court",
        "capacity": 2000,
        "area_sqm": 1200,
        "position": {"x": 50, "y": 75},
        "is_covered": True,
        "type": "amenity",
        "assigned_stands": [],
    },
    {
        "zone_id": "parking",
        "zone_name": "Parking Area",
        "capacity": 3000,
        "area_sqm": 8000,
        "position": {"x": 50, "y": 95},
        "is_covered": False,
        "type": "amenity",
        "assigned_stands": [],
    },
    {
        "zone_id": "main_entrance",
        "zone_name": "Main Entrance",
        "capacity": 1500,
        "area_sqm": 800,
        "position": {"x": 50, "y": 100},
        "is_covered": False,
        "type": "entrance",
        "assigned_stands": [],
    },
]


# ─── Gate-to-Stand Routing ────────────────────────────────────
# Maps each stand to its primary and alternate gates

STAND_GATE_ROUTING = {
    "North Stand": {
        "primary_gates": ["Gate 3", "Gate 4"],
        "alternate_gates": ["Gate 2"],
    },
    "South Stand": {
        "primary_gates": ["Gate 1", "Gate 5"],
        "alternate_gates": ["Gate 2"],
    },
    "East Stand": {
        "primary_gates": ["Gate 2", "Gate 5"],
        "alternate_gates": ["Gate 4"],
    },
    "West Stand": {
        "primary_gates": ["Gate 1"],
        "alternate_gates": ["Gate 3"],
    },
}


# ─── Emergency Routes ────────────────────────────────────────

EMERGENCY_ROUTES = [
    {
        "route_id": "ER1",
        "name": "North Emergency Corridor",
        "from_zones": ["North Stand", "Gate 3", "Gate 4"],
        "to_zone": "Parking Area",
        "medical_room": "Medical Room 1",
        "distance_meters": 200,
    },
    {
        "route_id": "ER2",
        "name": "South Emergency Corridor",
        "from_zones": ["South Stand", "Gate 1", "Food Court"],
        "to_zone": "Main Entrance",
        "medical_room": "Medical Room 2",
        "distance_meters": 150,
    },
    {
        "route_id": "ER3",
        "name": "East Emergency Exit",
        "from_zones": ["East Stand", "Gate 5"],
        "to_zone": "Parking Area",
        "medical_room": "Medical Room 1",
        "distance_meters": 250,
    },
    {
        "route_id": "ER4",
        "name": "West Emergency Exit",
        "from_zones": ["West Stand", "Gate 2"],
        "to_zone": "Main Entrance",
        "medical_room": "Medical Room 2",
        "distance_meters": 180,
    },
]


# ─── Staff Configuration ─────────────────────────────────────

STAFF_CONFIG = {
    "total_security": 320,
    "total_volunteers": 150,
    "total_medical": 20,
    "security_per_gate": 15,
    "volunteers_per_gate": 8,
    "medical_rooms": 2,
    "ambulances": 3,
}


# ─── Demo Scenario Config ────────────────────────────────────
# The scripted scenario for the demo presentation

DEMO_SCENARIO = {
    "title": "Pre-Match Metro Rush + Rain",
    "description": (
        "30 minutes before an IPL match. Gate 2 suddenly becomes overcrowded "
        "because 42% of East Stand users are arriving from the same metro exit. "
        "At the same time, rain is expected in 12 minutes."
    ),
    "phases": [
        {
            "phase": 1,
            "time_label": "T-30 min",
            "description": "Normal pre-match entry. All gates balanced.",
            "gate_crowds": {"Gate 1": 200, "Gate 2": 250, "Gate 3": 180, "Gate 4": 150, "Gate 5": 160},
            "weather": "clear",
            "alerts": [],
        },
        {
            "phase": 2,
            "time_label": "T-25 min",
            "description": "Metro train arrives. East Stand crowd surges to Gate 2.",
            "gate_crowds": {"Gate 1": 220, "Gate 2": 580, "Gate 3": 200, "Gate 4": 160, "Gate 5": 170},
            "weather": "cloudy",
            "alerts": ["crowd_surge_gate2"],
        },
        {
            "phase": 3,
            "time_label": "T-20 min",
            "description": "Gate 2 bottleneck. Rain forecast detected.",
            "gate_crowds": {"Gate 1": 250, "Gate 2": 820, "Gate 3": 220, "Gate 4": 170, "Gate 5": 180},
            "weather": "rain_expected_12min",
            "alerts": ["crowd_surge_gate2", "weather_rain"],
        },
        {
            "phase": 4,
            "time_label": "T-15 min",
            "description": "AI reroutes fans. Volunteers dispatched. Gate 4 opened extra lane.",
            "gate_crowds": {"Gate 1": 280, "Gate 2": 500, "Gate 3": 300, "Gate 4": 420, "Gate 5": 250},
            "weather": "light_rain",
            "alerts": ["reroute_active", "volunteers_dispatched"],
        },
        {
            "phase": 5,
            "time_label": "T-10 min",
            "description": "Situation stabilized. Crowd balanced across gates.",
            "gate_crowds": {"Gate 1": 300, "Gate 2": 350, "Gate 3": 320, "Gate 4": 380, "Gate 5": 300},
            "weather": "light_rain",
            "alerts": ["situation_stabilized"],
        },
    ],
}
