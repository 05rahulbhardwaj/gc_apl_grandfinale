"""
CrowdPulse AI - Weather Service
Fetches real-time weather data from the Open-Meteo API.
Caches results for 5 minutes to avoid excessive API calls.
"""

import time
import logging
import threading
from datetime import datetime
from typing import Optional

import requests

from backend.config import STADIUM_LAT, STADIUM_LON, WEATHER_CACHE_SECONDS
from backend.models import WeatherData

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes → human-readable descriptions
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}


class WeatherService:
    """Fetches and caches weather data from Open-Meteo."""

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(
        self,
        latitude: float = STADIUM_LAT,
        longitude: float = STADIUM_LON,
        cache_seconds: int = WEATHER_CACHE_SECONDS,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.cache_seconds = cache_seconds

        self._cached_data: Optional[WeatherData] = None
        self._cache_timestamp: float = 0.0
        self._lock = threading.Lock()

    # ── public API ────────────────────────────────────────────

    def get_weather(self) -> WeatherData:
        """Return current weather, using cache if still fresh."""
        with self._lock:
            now = time.time()
            if (
                self._cached_data is not None
                and (now - self._cache_timestamp) < self.cache_seconds
            ):
                return self._cached_data

        # Cache miss – fetch fresh data (outside the lock to avoid blocking)
        data = self._fetch_weather()

        with self._lock:
            self._cached_data = data
            self._cache_timestamp = time.time()

        return data

    # ── private helpers ───────────────────────────────────────

    def _fetch_weather(self) -> WeatherData:
        """Call Open-Meteo and parse the response into a WeatherData model."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current_weather": "true",
            "hourly": "precipitation_probability,relative_humidity_2m",
            "timezone": "auto",
            "forecast_days": 1,
        }

        try:
            resp = requests.get(self.OPEN_METEO_URL, params=params, timeout=10)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            logger.warning("Weather API request failed: %s – returning defaults", exc)
            return WeatherData(last_updated=datetime.now())

        try:
            cw = payload.get("current_weather", {})
            hourly = payload.get("hourly", {})

            weather_code = int(cw.get("weathercode", 0))
            description = WMO_CODES.get(weather_code, "Unknown")
            is_raining = weather_code in RAIN_CODES

            # Precipitation probability for next few hours
            precip_probs = hourly.get("precipitation_probability", [])
            humidity_vals = hourly.get("relative_humidity_2m", [])

            # Current hour index: the first entry whose time matches
            current_hour_index = 0
            current_time_str = cw.get("time", "")
            hourly_times = hourly.get("time", [])
            for i, t in enumerate(hourly_times):
                if t.startswith(current_time_str[:13]):  # match YYYY-MM-DDTHH
                    current_hour_index = i
                    break

            rain_prob_now = 0.0
            if precip_probs and current_hour_index < len(precip_probs):
                rain_prob_now = float(precip_probs[current_hour_index] or 0)

            humidity_now = 65.0
            if humidity_vals and current_hour_index < len(humidity_vals):
                humidity_now = float(humidity_vals[current_hour_index] or 65)

            # Estimate when rain is expected (in minutes) by scanning future hours
            forecast_rain_minutes: Optional[int] = None
            if not is_raining:
                for offset in range(1, min(6, len(precip_probs) - current_hour_index)):
                    idx = current_hour_index + offset
                    if idx < len(precip_probs) and (precip_probs[idx] or 0) > 50:
                        forecast_rain_minutes = offset * 60  # rough estimate
                        break

            return WeatherData(
                temperature=float(cw.get("temperature", 28)),
                humidity=humidity_now,
                wind_speed=float(cw.get("windspeed", 12)),
                wind_direction=float(cw.get("winddirection", 180)),
                rain_probability=rain_prob_now,
                weather_code=weather_code,
                weather_description=description,
                is_raining=is_raining,
                forecast_rain_minutes=forecast_rain_minutes,
                last_updated=datetime.now(),
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse weather response: %s", exc)
            return WeatherData(last_updated=datetime.now())

    def invalidate_cache(self) -> None:
        """Force next call to fetch fresh data."""
        with self._lock:
            self._cache_timestamp = 0.0
