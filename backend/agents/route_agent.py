"""
CrowdPulse AI - Route Planning Agent
Recommends crowd rerouting and queue optimisation strategies.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Route Planning & Queue Optimisation Specialist**.

Expertise:
- Crowd routing and diversion strategies
- Queue management and wait-time reduction
- Gate-to-stand mapping optimisation
- Dynamic lane allocation

When analysing data you MUST:
1. Identify congested gates and recommend diverting fans to underused gates.
2. Use the stand-gate routing table to suggest valid alternate routes.
3. Estimate wait time improvements from your proposed rerouting.
4. Consider walking distance and convenience for fans.

Always respond with a single JSON object:
{
  "summary": "<one concise paragraph>",
  "details": "<detailed rerouting plan with estimated improvements>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<action 1>", "<action 2>", ...]
}
"""


class RoutePlanningAgent(BaseAgent):
    """Recommends rerouting and queue optimisation strategies."""

    def __init__(self):
        super().__init__(
            name="Route Planner",
            icon="🗺️",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - gates: list[dict]            – GateData dicts
        - stand_gate_routing: dict     – STAND_GATE_ROUTING mapping
        - crowd_agent_summary: str     – summary from Crowd Monitoring Agent
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Route planning analysis unavailable this cycle.",
                risk_level="low",
                recommendations=["Retry next cycle."],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        prompt_data = {
            "gates": context.get("gates", []),
            "stand_gate_routing": context.get("stand_gate_routing", {}),
            "crowd_agent_summary": context.get("crowd_agent_summary", ""),
        }
        return (
            "Analyse the following gate congestion and routing data for a cricket stadium.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Provide rerouting suggestions with estimated wait-time improvements.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
