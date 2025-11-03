"""
AutoGen agents for Clínica Luana multi-agent scheduling system.

This module contains all specialized agents:
- Supervisor: Intent classification and routing
- Intake: Contact information collection
- FAQ: Questions about treatments, prices, policies
- Scheduler: Appointment booking, rescheduling, cancellation
- Escalation: Handoff to human agents

Each agent is designed to work with AutoGen's ConversableAgent framework
and integrates with the tools defined in the tools/ module.
"""

from agents.supervisor import SupervisorAgent, create_supervisor_agent
from agents.intake import IntakeAgent, create_intake_agent
from agents.faq import FAQAgent, create_faq_agent
from agents.scheduler import SchedulerAgent, create_scheduler_agent
from agents.escalation import EscalationAgent, create_escalation_agent

__all__ = [
    # Agent classes
    "SupervisorAgent",
    "IntakeAgent",
    "FAQAgent",
    "SchedulerAgent",
    "EscalationAgent",
    # Factory functions
    "create_supervisor_agent",
    "create_intake_agent",
    "create_faq_agent",
    "create_scheduler_agent",
    "create_escalation_agent",
]
