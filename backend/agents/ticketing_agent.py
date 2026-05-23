"""
CrowdPulse AI - Ticketing & Entry Agent
Analyses ticket scan events, detects fraud / duplicates, and flags gate
imbalances.
"""

import json
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.models import AgentResponse

SYSTEM_PROMPT = """\
You are CrowdPulse AI's **Ticketing & Entry Control Specialist**.

Expertise:
- Venue access control and ticket validation
- Fraud detection (fake tickets, duplicate scans)
- Gate throughput analysis and entry delays
- Fan flow optimisation at entry points

When analysing data you MUST:
1. Flag any gates with scan rates below 50 % of capacity as underutilised.
2. Highlight duplicate or invalid ticket scan attempts.
3. Detect if one gate is handling a disproportionate share of entries.
4. Recommend rebalancing when wait times exceed 8 minutes at any gate.

Always respond with a single JSON object:
{
  "summary": "<one concise paragraph>",
  "details": "<detailed gate-by-gate and ticket analysis>",
  "risk_level": "low" | "medium" | "high" | "critical",
  "recommendations": ["<action 1>", "<action 2>", ...]
}
"""


class TicketingEntryAgent(BaseAgent):
    """Analyses ticket scans, entry delays, and fraud indicators."""

    def __init__(self):
        super().__init__(
            name="Ticketing Agent",
            icon="🎫",
            system_prompt=SYSTEM_PROMPT,
        )

    def analyze(self, context: dict) -> AgentResponse:
        """
        Parameters expected in *context*:
        - ticket_scans: list[dict]     – recent TicketScanEvent dicts
        - gates: list[dict]            – GateData dicts with entry rates
        - duplicate_attempts: int      – count of duplicate scans
        - invalid_attempts: int        – count of fake/invalid scans
        - scan_rate_per_min: float     – overall scans per minute
        """
        enriched = self._build_user_message(context)
        response_json = self._call_llm(enriched)
        if response_json is None:
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Ticketing analysis unavailable this cycle.",
                risk_level="low",
                recommendations=["Retry next cycle."],
            )
        return self._parse_response(response_json)

    def _build_user_message(self, context: dict) -> str:
        prompt_data = {
            "ticket_scans": context.get("ticket_scans", []),
            "gates": context.get("gates", []),
            "duplicate_attempts": context.get("duplicate_attempts", 0),
            "invalid_attempts": context.get("invalid_attempts", 0),
            "scan_rate_per_min": context.get("scan_rate_per_min", 0),
        }
        return (
            "Analyse the following ticketing and entry data for a cricket stadium.\n\n"
            f"```json\n{json.dumps(prompt_data, indent=2, default=str)}\n```\n\n"
            "Identify entry delays, fake ticket attempts, and gate imbalances.\n"
            "Respond ONLY with a JSON object: "
            '{"summary", "details", "risk_level", "recommendations"}.'
        )
