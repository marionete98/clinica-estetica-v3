"""
Domain-specific repository modules.
"""

from .appointments import (
    create_appointment,
    get_appointment_by_id,
    get_appointments_by_contact,
    mark_reminder_sent,
    reschedule_appointment,
    update_appointment_status,
)
from .availability import list_available_slots
from .contacts import (
    create_or_update_contact,
    get_contact_by_id,
    get_contact_by_phone,
    increment_no_show_count,
)
from .knowledge_base import get_message_template, search_knowledge_base
from .logs import create_log_entry
from .services import get_service_by_id, list_active_services
from .sessions import create_or_update_session, get_session_by_conversation_id

__all__ = [
    "create_or_update_contact",
    "get_contact_by_phone",
    "get_contact_by_id",
    "increment_no_show_count",
    "create_appointment",
    "get_appointment_by_id",
    "get_appointments_by_contact",
    "update_appointment_status",
    "reschedule_appointment",
    "mark_reminder_sent",
    "list_available_slots",
    "create_or_update_session",
    "get_session_by_conversation_id",
    "create_log_entry",
    "get_service_by_id",
    "list_active_services",
    "search_knowledge_base",
    "get_message_template",
]
