"""
CrowdPulse AI - Emergency Response Agent
Evaluates all agent outputs and produces emergency corridor / evacuation plans.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Emergency Response & Safety Specialist**.

Expertise:
- Stadium emergency management and safety protocols
- Evacuation route planning and crowd control
- Staff dispatch and medical resource allocation
- Stampede prevention and de-escalation

When analysing data you MUST:
1. Review all other agents' assessments for any HIGH or CRITICAL risk.
2. If any zone has a stampede-risk flag, recommend immediate action.
3. Map alerts to the nearest emergency routes and medical rooms.
4. Recommend precise staff dispatch numbers and locations.
5. Only recommend evacuation when risk is CRITICAL — otherwise focus on de-escalation.

Always respond with a single JSON object:
{
  "summary": "<one concise paragraph>",
  "details": "<detailed emergency assessment with staff/route specifics>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<action 1>", "<action 2>", ...]
}
"""


class EmergencyResponseAgent(BaseAgent):
    """Evaluates combined agent outputs and produces emergency plans."""

    def __init__(self):
        super().__init__(
            name="Emergency Response",
            icon="🚨",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - agent_summaries: list[dict]  – summaries from all prior agents
        - alerts: list[dict]           – current active alerts
        - emergency_routes: list[dict] – EMERGENCY_ROUTES config
        - staff_config: dict           – STAFF_CONFIG
        - zones: list[dict]            – zone data
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Emergency analysis unavailable this cycle.",
                risk_level="low",
                recommendations=["Retry next cycle."],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        prompt_data = {
            "agent_summaries": context.get("agent_summaries", []),
            "active_alerts": context.get("alerts", []),
            "emergency_routes": context.get("emergency_routes", []),
            "staff_config": context.get("staff_config", {}),
            "zones": context.get("zones", []),
        }
        return (
            "You are receiving the combined output of all CrowdPulse AI agents "
            "plus the stadium emergency configuration.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Determine if an emergency protocol is needed. Provide emergency corridors, "
            "staff dispatch, and evacuation recommendations.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
