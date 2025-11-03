from typing import Literal, Optional
from pydantic import BaseModel


class RouteDecision(BaseModel):
    agent: Literal["intake", "faq", "scheduler", "escalation"]
    confidence: Literal["low", "high"]
    reasoning: str


class SchedulerAction(BaseModel):
    action: Literal[
        "booking_created",
        "booking_cancelled",
        "booking_rescheduled",
        "slots_listed",
        "info_provided",
    ]
    booking_id: Optional[str] = None
    requires_confirmation: bool
    response: str

