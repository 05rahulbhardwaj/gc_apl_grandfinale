"""
CrowdPulse AI - Base Agent
Abstract base for all LLM-powered agents.  Talks to Groq via the OpenAI SDK.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional

from openai import OpenAI, APIError, RateLimitError, APITimeoutError

from backend.config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL
from backend.models import AgentResponse, RiskLevel

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY = 2.0  # seconds between retries


class BaseAgent:
    """
    Base class for all CrowdPulse AI agents.

    Sub-classes set *name*, *icon*, and *system_prompt* and may override
    ``_build_user_message()`` to customise what gets sent to the LLM.
    """

    def __init__(self, name: str, icon: str, system_prompt: str):
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt

        self._client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )

    # ── public API ────────────────────────────────────────────

    def analyze(self, context: dict) -> AgentResponse:
        """
        Send *context* to the LLM and return a structured AgentResponse.
        Retries up to MAX_RETRIES times on transient errors.
        """
        user_message = self._build_user_message(context)
        response_json = self._call_llm(user_message)

        if response_json is None:
            # Fallback when LLM is unreachable
            return AgentResponse(
                agent_name=self.name,
                agent_icon=self.icon,
                timestamp=datetime.now(),
                summary="Analysis unavailable – LLM call failed.",
                details="The agent could not reach the language model.",
                risk_level=RiskLevel.LOW,
                recommendations=["Retry analysis in the next cycle."],
            )

        return self._parse_response(response_json)

    # ── overridable helpers ───────────────────────────────────

    def _build_user_message(self, context: dict) -> str:
        """Format the context dict into a prompt string for the LLM."""
        return (
            "Analyze the following stadium data and provide your assessment.\n\n"
            f"```json\n{json.dumps(context, indent=2, default=str)}\n```\n\n"
            "Respond ONLY with a JSON object in this exact schema:\n"
            "{\n"
            '  "summary": "<one-paragraph summary>",\n'
            '  "details": "<detailed analysis>",\n'
            '  "risk_level": "low" | "medium" | "high" | "critical",\n'
            '  "recommendations": ["<action 1>", "<action 2>", ...]\n'
            "}\n"
        )

    # ── LLM call with retries ─────────────────────────────────

    def _call_llm(self, user_message: str) -> Optional[dict]:
        """Call Groq / OpenAI-compatible endpoint with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 2):  # 1-based, +1 for initial try
            try:
                chat_completion = self._client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )

                raw_text = chat_completion.choices[0].message.content or "{}"
                return json.loads(raw_text)

            except (RateLimitError, APITimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "[%s] Transient LLM error (attempt %d/%d): %s",
                    self.name, attempt, MAX_RETRIES + 1, exc,
                )
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)

            except APIError as exc:
                last_error = exc
                logger.error("[%s] LLM API error: %s", self.name, exc)
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

            except json.JSONDecodeError as exc:
                last_error = exc
                logger.error("[%s] LLM returned invalid JSON: %s", self.name, exc)
                break  # no point retrying a parse error from a bad model answer

            except Exception as exc:
                last_error = exc
                logger.error("[%s] Unexpected error: %s", self.name, exc)
                break

        logger.error(
            "[%s] All LLM retries exhausted. Last error: %s", self.name, last_error
        )
        return None

    # ── response parsing ──────────────────────────────────────

    def _parse_response(self, data: dict) -> AgentResponse:
        """Turn the JSON dict returned by the LLM into an AgentResponse."""
        risk_str = str(data.get("risk_level", "low")).lower()
        try:
            risk_level = RiskLevel(risk_str)
        except ValueError:
            risk_level = RiskLevel.LOW

        recommendations = data.get("recommendations", [])
        if isinstance(recommendations, str):
            recommendations = [recommendations]

        return AgentResponse(
            agent_name=self.name,
            agent_icon=self.icon,
            timestamp=datetime.now(),
            summary=str(data.get("summary", "")),
            details=str(data.get("details", "")),
            risk_level=risk_level,
            recommendations=[str(r) for r in recommendations],
        )
