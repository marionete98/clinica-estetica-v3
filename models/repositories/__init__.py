"""Domain-specific repository helpers and factories."""

from .appointments import (
    AppointmentRepository,
    create_appointment,
    get_appointment_by_id,
    get_appointment_repository,
    get_appointments_by_contact,
    mark_reminder_sent,
    reschedule_appointment,
    update_appointment_status,
)
from .availability import list_available_slots
from .contacts import (
    ContactRepository,
    create_or_update_contact,
    get_contact_by_id,
    get_contact_by_phone,
    get_contact_repository,
    increment_no_show_count,
    update_contact,
)
from .knowledge_base import (
    KnowledgeBaseRepository,
    get_knowledge_base_repository,
    get_message_template,
    search_knowledge_base,
)
from .logs import create_log_entry
from .sessions import (
    SessionRepository,
    create_or_update_session,
    get_session_by_conversation_id,
    get_session_repository,
)
from .services import (
    ServiceRepository,
    get_service_by_id,
    get_service_repository,
    list_active_services,
)
from .template_repository import TemplateRepository, get_template_repository

__all__ = [
    "AppointmentRepository",
    "ContactRepository",
    "KnowledgeBaseRepository",
    "ServiceRepository",
    "SessionRepository",
    "TemplateRepository",
    "create_or_update_contact",
    "get_contact_by_phone",
    "get_contact_by_id",
    "update_contact",
    "increment_no_show_count",
    "create_appointment",
    "get_appointment_by_id",
    "get_appointments_by_contact",
    "update_appointment_status",
    "reschedule_appointment",
    "mark_reminder_sent",
    "list_available_slots",
    "search_knowledge_base",
    "get_message_template",
    "create_or_update_session",
    "get_session_by_conversation_id",
    "get_appointment_repository",
    "get_contact_repository",
    "get_session_repository",
    "get_knowledge_base_repository",
    "get_service_repository",
    "get_service_by_id",
    "list_active_services",
    "create_log_entry",
    "get_template_repository",
]
