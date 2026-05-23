"""
CrowdPulse AI - Weather Risk Agent
Assesses weather impact on outdoor events and spectator safety.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Weather Risk Assessment Specialist**.

Expertise:
- Impact of weather on outdoor sporting events
- Spectator safety during rain, storms, and extreme heat
- Capacity adjustments for covered vs uncovered zones
- Lightning and wind speed risk thresholds

When analysing data you MUST:
1. Assess rain probability and its impact on uncovered zones.
2. Check wind speed — flag anything above 50 km/h as dangerous.
3. Consider temperature extremes (above 40 °C or below 5 °C).
4. Recommend shifting fans from uncovered to covered areas if rain is imminent.
5. Note if a weather forecast predicts deterioration within the match window.

Always respond with a single JSON object:
{
  "summary": "<one concise paragraph>",
  "details": "<detailed weather risk breakdown>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<action 1>", "<action 2>", ...]
}
"""


class WeatherRiskAgent(BaseAgent):
    """Assesses weather risk and recommends capacity adjustments."""

    def __init__(self):
        super().__init__(
            name="Weather Risk",
            icon="🌦️",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - weather: dict                – WeatherData dict
        - zones: list[dict]            – ZoneStatus dicts (includes is_covered)
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Weather risk analysis unavailable this cycle.",
                risk_level="low",
                recommendations=["Retry next cycle."],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        weather = context.get("weather", {})
        zones = context.get("zones", [])
        covered = [z for z in zones if z.get("is_covered")]
        uncovered = [z for z in zones if not z.get("is_covered")]

        prompt_data = {
            "weather": weather,
            "covered_zones": [z.get("zone_name") for z in covered],
            "uncovered_zones": [z.get("zone_name") for z in uncovered],
            "zone_details": zones,
        }
        return (
            "Analyse the following weather and zone data for a cricket stadium.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Provide a weather risk assessment and capacity adjustments for covered areas.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
