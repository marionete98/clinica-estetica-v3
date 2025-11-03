import pytest
from pydantic import ValidationError

from models.agent_schemas import RouteDecision, SchedulerAction


class TestRouteDecisionModel:
    def test_valid_route_decision(self):
        rd = RouteDecision(agent="faq", confidence="high", reasoning="Pergunta informativa")
        assert rd.agent == "faq"
        assert rd.confidence == "high"
        assert isinstance(rd.reasoning, str)

    def test_invalid_agent_raises(self):
        with pytest.raises(ValidationError):
            RouteDecision(agent="unknown", confidence="low", reasoning="...")

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValidationError):
            RouteDecision(agent="faq", confidence="medium", reasoning="...")


class TestSchedulerActionModel:
    def test_valid_scheduler_action_minimal(self):
        sa = SchedulerAction(
            action="info_provided",
            requires_confirmation=False,
            response="Aqui estão as informações."
        )
        assert sa.action == "info_provided"
        assert sa.booking_id is None
        assert sa.requires_confirmation is False
        assert isinstance(sa.response, str)

    def test_invalid_action_raises(self):
        with pytest.raises(ValidationError):
            SchedulerAction(
                action="invalid",
                requires_confirmation=True,
                response="..."
            )

