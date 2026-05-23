"""
CrowdPulse AI - Agent Orchestrator
Runs all six specialist agents in sequence, feeds context forward, and
synthesises a unified ActionPlan with an overall safety score.
"""

import logging
from datetime import datetime

from backend.agents.crowd_agent import CrowdMonitoringAgent
from backend.agents.ticketing_agent import TicketingEntryAgent
from backend.agents.route_agent import RoutePlanningAgent
from backend.agents.weather_agent import WeatherRiskAgent
from backend.agents.emergency_agent import EmergencyResponseAgent
from backend.agents.fan_comm_agent import FanCommunicationAgent
from backend.models import (
    AgentResponse,
    ActionPlan,
    ActionItem,
    ActionType,
    RiskLevel,
    StadiumState,
)
from backend.utils.stadium_config import (
    STAND_GATE_ROUTING,
    EMERGENCY_ROUTES,
    STAFF_CONFIG,
)

logger = logging.getLogger(__name__)

# Risk level → numeric weight for averaging
_RISK_WEIGHT = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


class AgentOrchestrator:
    """Runs all agents in sequence and produces a unified ActionPlan."""

    def __init__(self):
        self.crowd_agent = CrowdMonitoringAgent()
        self.ticketing_agent = TicketingEntryAgent()
        self.route_agent = RoutePlanningAgent()
        self.weather_agent = WeatherRiskAgent()
        self.emergency_agent = EmergencyResponseAgent()
        self.fan_comm_agent = FanCommunicationAgent()

        logger.info("AgentOrchestrator initialised with 6 agents")

    # ── main entry point ──────────────────────────────────────

    def run_cycle(
        self, stadium_state: StadiumState
    ) -> tuple[list[AgentResponse], ActionPlan]:
        """
        Execute one full analysis cycle:
        crowd → ticketing → route → weather → emergency → fan_comm

        Returns (list_of_agent_responses, unified_action_plan).
        """
        responses: list[AgentResponse] = []
        agent_summaries: list[dict] = []

        state_dict = stadium_state.model_dump(mode="json")
        zones = state_dict.get("zones", [])
        gates = state_dict.get("gates", [])
        weather = state_dict.get("weather", {})
        alerts = state_dict.get("alerts", [])

        # ── 1. Crowd Monitoring Agent ─────────────────────────
        logger.info("Running Crowd Monitoring Agent …")
        crowd_ctx = {
            "zones": zones,
            "gates": gates,
            "yolo_person_count": stadium_state.total_crowd_inside,
            "phase_description": state_dict.get("match_info", {}).get("status", ""),
        }
        crowd_resp = self.crowd_agent.analyze(crowd_ctx)
        responses.append(crowd_resp)
        agent_summaries.append(self._summary_dict(crowd_resp))

        # ── 2. Ticketing & Entry Agent ────────────────────────
        logger.info("Running Ticketing Agent …")
        # Collect ticket scan info from live_updates (lightweight)
        ticket_ctx = {
            "ticket_scans": [],  # populated by caller if available
            "gates": gates,
            "duplicate_attempts": 0,
            "invalid_attempts": 0,
            "scan_rate_per_min": stadium_state.ticket_scans_per_min,
        }
        ticketing_resp = self.ticketing_agent.analyze(ticket_ctx)
        responses.append(ticketing_resp)
        agent_summaries.append(self._summary_dict(ticketing_resp))

        # ── 3. Route Planning Agent ───────────────────────────
        logger.info("Running Route Planning Agent …")
        route_ctx = {
            "gates": gates,
            "stand_gate_routing": STAND_GATE_ROUTING,
            "crowd_agent_summary": crowd_resp.summary,
        }
        route_resp = self.route_agent.analyze(route_ctx)
        responses.append(route_resp)
        agent_summaries.append(self._summary_dict(route_resp))

        # ── 4. Weather Risk Agent ─────────────────────────────
        logger.info("Running Weather Risk Agent …")
        weather_ctx = {
            "weather": weather,
            "zones": zones,
        }
        weather_resp = self.weather_agent.analyze(weather_ctx)
        responses.append(weather_resp)
        agent_summaries.append(self._summary_dict(weather_resp))

        # ── 5. Emergency Response Agent ───────────────────────
        logger.info("Running Emergency Response Agent …")
        emergency_ctx = {
            "agent_summaries": agent_summaries,
            "alerts": alerts,
            "emergency_routes": EMERGENCY_ROUTES,
            "staff_config": STAFF_CONFIG,
            "zones": zones,
        }
        emergency_resp = self.emergency_agent.analyze(emergency_ctx)
        responses.append(emergency_resp)
        agent_summaries.append(self._summary_dict(emergency_resp))

        # ── 6. Fan Communication Agent ────────────────────────
        logger.info("Running Fan Communication Agent …")
        overall_risk = self._compute_overall_risk(responses)
        fan_ctx = {
            "action_plan_summary": emergency_resp.summary,
            "agent_summaries": agent_summaries,
            "overall_risk": overall_risk.value,
            "alerts": alerts,
        }
        fan_resp = self.fan_comm_agent.analyze(fan_ctx)
        responses.append(fan_resp)

        # ── Synthesise ActionPlan ─────────────────────────────
        action_plan = self._build_action_plan(responses, overall_risk, fan_resp)

        logger.info(
            "Orchestration cycle complete – risk=%s  safety=%d",
            action_plan.overall_risk.value,
            action_plan.safety_score,
        )
        return responses, action_plan

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    def _summary_dict(resp: AgentResponse) -> dict:
        return {
            "agent": resp.agent_name,
            "summary": resp.summary,
            "risk_level": resp.risk_level.value if isinstance(resp.risk_level, RiskLevel) else str(resp.risk_level),
            "recommendations": resp.recommendations,
        }

    @staticmethod
    def _compute_overall_risk(responses: list[AgentResponse]) -> RiskLevel:
        """
        Overall risk = highest individual risk, unless only one agent is
        high and the rest are low — in that case, cap at MEDIUM.
        """
        if not responses:
            return RiskLevel.LOW

        levels = []
        for r in responses:
            rl = r.risk_level
            if isinstance(rl, str):
                try:
                    rl = RiskLevel(rl)
                except ValueError:
                    rl = RiskLevel.LOW
            levels.append(rl)

        max_level = max(levels, key=lambda l: _RISK_WEIGHT.get(l, 1))

        # If only one agent reports HIGH and rest are LOW, cap at MEDIUM
        if max_level == RiskLevel.HIGH:
            high_count = sum(1 for l in levels if l == RiskLevel.HIGH)
            low_count = sum(1 for l in levels if l == RiskLevel.LOW)
            if high_count == 1 and low_count == len(levels) - 1:
                return RiskLevel.MEDIUM

        return max_level

    @staticmethod
    def _compute_safety_score(overall_risk: RiskLevel) -> int:
        """Map risk level to a 0-100 safety score with some variance."""
        import random
        base = {
            RiskLevel.LOW: 85,
            RiskLevel.MEDIUM: 65,
            RiskLevel.HIGH: 40,
            RiskLevel.CRITICAL: 15,
        }
        return min(100, max(0, base.get(overall_risk, 78) + random.randint(-5, 5)))

    def _build_action_plan(
        self,
        responses: list[AgentResponse],
        overall_risk: RiskLevel,
        fan_resp: AgentResponse,
    ) -> ActionPlan:
        """Merge agent recommendations into a single ActionPlan."""
        actions: list[ActionItem] = []
        action_id = 1

        # Map recommendation keywords to ActionTypes
        keyword_map = {
            "reroute": ActionType.NOTIFY_FANS,
            "divert": ActionType.NOTIFY_FANS,
            "notify": ActionType.NOTIFY_FANS,
            "message": ActionType.NOTIFY_FANS,
            "dispatch": ActionType.DISPATCH_STAFF,
            "staff": ActionType.DISPATCH_STAFF,
            "volunteer": ActionType.DISPATCH_STAFF,
            "open": ActionType.OPEN_GATE,
            "gate": ActionType.OPEN_GATE,
            "lane": ActionType.OPEN_GATE,
            "increase": ActionType.INCREASE_STAFF,
            "add": ActionType.INCREASE_STAFF,
            "evacuate": ActionType.EMERGENCY_PROTOCOL,
            "emergency": ActionType.EMERGENCY_PROTOCOL,
            "stampede": ActionType.EMERGENCY_PROTOCOL,
            "maintain": ActionType.MAINTAIN_ACCESS,
        }

        for resp in responses:
            for rec in resp.recommendations:
                # Determine action type from keywords
                action_type = ActionType.NOTIFY_FANS  # default
                rec_lower = rec.lower()
                for keyword, at in keyword_map.items():
                    if keyword in rec_lower:
                        action_type = at
                        break

                actions.append(
                    ActionItem(
                        action_id=action_id,
                        action_type=action_type,
                        description=rec,
                        priority=resp.risk_level if isinstance(resp.risk_level, RiskLevel) else RiskLevel.LOW,
                        is_executed=False,
                    )
                )
                action_id += 1

        # Build messages from fan comm agent
        fan_recs = fan_resp.recommendations
        fan_message = fan_recs[0] if len(fan_recs) > 0 else "Enjoy the match! 🏏"
        volunteer_message = fan_recs[1] if len(fan_recs) > 1 else "Maintain positions."
        security_message = fan_recs[2] if len(fan_recs) > 2 else "Standard patrol."

        # Risk reason from emergency agent
        emergency_resp = next(
            (r for r in responses if r.agent_name == "Emergency Response"), None
        )
        risk_reason = emergency_resp.summary if emergency_resp else ""

        safety_score = self._compute_safety_score(overall_risk)

        return ActionPlan(
            overall_risk=overall_risk,
            risk_reason=risk_reason,
            safety_score=safety_score,
            actions=actions,
            fan_message=fan_message,
            volunteer_message=volunteer_message,
            security_message=security_message,
            expected_impact=f"Safety score: {safety_score}/100. "
            f"{len(actions)} actions recommended.",
            timestamp=datetime.now(),
        )
