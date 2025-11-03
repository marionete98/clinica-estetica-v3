"""TypedDict definitions used across agents and orchestration layers."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict


class AgentResponse(TypedDict, total=False):
    response: str
    agent: str
    confidence: Literal["high", "medium", "low"]
    metadata: Dict[str, object]


class SupervisorClassification(TypedDict):
    intent: str
    agent: str
    loop_detected: bool
    confidence: float


class FAQResponse(AgentResponse, total=False):
    sources: List[str]
    template_used: Optional[str]


class SchedulerResponse(AgentResponse, total=False):
    action: str
    booking_id: Optional[str]
    slots: Optional[List[Dict[str, object]]]


class EscalationResponse(AgentResponse, total=False):
    reason: str
    priority: Literal["low", "medium", "high"]
    summary: str


__all__ = [
    "AgentResponse",
    "SupervisorClassification",
    "FAQResponse",
    "SchedulerResponse",
    "EscalationResponse",
]
