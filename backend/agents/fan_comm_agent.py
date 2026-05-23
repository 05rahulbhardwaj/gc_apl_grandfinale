"""
CrowdPulse AI - Fan Communication Agent
Generates clear, fan-friendly messages, volunteer instructions, and security
briefings based on the decisions made by the other agents.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Fan Communication & Crisis Messaging Specialist**.

Expertise:
- Clear, calm public messaging during stadium events
- Multilingual crowd communication best practices
- Volunteer and security staff briefing templates
- De-escalation language and positive crowd guidance

When producing messages you MUST:
1. Write a short, reassuring message for fans displayed on screens/apps.
   Keep it under 50 words. Use simple language. Avoid panic-inducing words.
2. Write concise volunteer instructions (what to do, where to go).
3. Write a security team briefing (precise, actionable).
4. Adjust tone based on risk level:
   - LOW: informational / friendly
   - MEDIUM: advisory / proactive
   - HIGH: directive / urgent
   - CRITICAL: emergency / commanding

Always respond with a single JSON object:
{
  "summary": "<the fan-facing message>",
  "details": "<volunteer instructions + security briefing combined>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<fan message>", "<volunteer instruction>", "<security briefing>"]
}
"""


class FanCommunicationAgent(BaseAgent):
    """Generates public-facing messages and staff briefings."""

    def __init__(self):
        super().__init__(
            name="Fan Communication",
            icon="📢",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - action_plan_summary: str       – overall action plan description
        - agent_summaries: list[dict]    – summaries from all prior agents
        - overall_risk: str              – current overall risk level
        - alerts: list[dict]             – active alerts
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Welcome to the stadium! Enjoy the match. 🏏",
                details="No specific instructions at this time.",
                risk_level="low",
                recommendations=[
                    "Welcome to the stadium! Enjoy the match.",
                    "Volunteers: maintain positions, assist fans as needed.",
                    "Security: standard patrol, no incidents reported.",
                ],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        prompt_data = {
            "action_plan_summary": context.get("action_plan_summary", ""),
            "agent_summaries": context.get("agent_summaries", []),
            "overall_risk": context.get("overall_risk", "low"),
            "active_alerts": context.get("alerts", []),
        }
        return (
            "Based on the following combined agent analysis and action plan, "
            "generate communication messages.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Produce: (1) a fan-facing message, (2) volunteer instructions, "
            "(3) a security briefing.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
