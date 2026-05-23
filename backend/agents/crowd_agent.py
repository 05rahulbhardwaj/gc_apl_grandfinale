"""
CrowdPulse AI - Crowd Monitoring Agent
Analyses zone densities, gate queues, and YOLO person counts to detect
overcrowding and surge patterns.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Crowd Monitoring Specialist**.

Expertise:
- Real-time crowd density analysis across stadium zones
- Surge detection and pattern recognition
- Density heatmap interpretation (people / m²)
- Predicting crowd build-up based on entry rates

When analysing data you MUST:
1. Identify any zone whose density exceeds 3.0 people/m² as "high" risk.
2. Flag any gate whose queue exceeds 500 people as congested.
3. Detect rapid increases in entry rate as potential surges.
4. Consider the capacity utilisation percentage of each zone.

Always respond with a single JSON object:
{
  "summary": "<one concise paragraph>",
  "details": "<detailed zone-by-zone breakdown>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<action 1>", "<action 2>", ...]
}
"""


class CrowdMonitoringAgent(BaseAgent):
    """Analyses crowd density, surge patterns, and zone utilisation."""

    def __init__(self):
        super().__init__(
            name="Crowd Monitor",
            icon="👥",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - zones: list[dict]           – ZoneStatus dicts
        - gates: list[dict]           – GateData dicts
        - yolo_person_count: int      – latest YOLO count from RTSP feed
        - phase_description: str      – current demo scenario description
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Crowd analysis unavailable this cycle.",
                risk_level="low",
                recommendations=["Retry next cycle."],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        zones = context.get("zones", [])
        gates = context.get("gates", [])
        yolo_count = context.get("yolo_person_count", 0)
        phase_desc = context.get("phase_description", "")

        prompt_data = {
            "scenario": phase_desc,
            "yolo_live_count": yolo_count,
            "zones": zones,
            "gates": gates,
        }
        return (
            "Analyse the following crowd data for a cricket stadium.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Identify overcrowded zones, surge patterns, and trends.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
