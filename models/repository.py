"""
Backwards compatible aggregator for repository operations.

The repository layer is now split into domain-specific modules under
`models.repositories`. This module re-exports the public API so existing
imports (`from models.repository import ...`) continue to work.
"""

from __future__ import annotations

from config.redis_client import create_redis_client
from config.supabase_client import (
    create_supabase_client,
    create_supabase_operations,
)

from models.repositories.appointments import (
    create_appointment,
    get_appointment_by_id,
    get_appointments_by_contact,
    mark_reminder_sent,
    reschedule_appointment,
    update_appointment_status,
)
from models.repositories.availability import list_available_slots
from models.repositories.contacts import (
    create_or_update_contact,
    get_contact_by_id,
    get_contact_by_phone,
    increment_no_show_count,
)
from models.repositories.knowledge_base import (
    get_message_template,
    search_knowledge_base,
)
from models.repositories.logs import create_log_entry
from models.repositories.services import (
    get_service_by_id,
    list_active_services,
)
from models.repositories.sessions import (
    create_or_update_session,
    get_session_by_conversation_id,
)

__all__ = [
    # Contacts
    "create_or_update_contact",
    "get_contact_by_phone",
    "get_contact_by_id",
    "increment_no_show_count",
    # Appointments
    "create_appointment",
    "get_appointment_by_id",
    "get_appointments_by_contact",
    "update_appointment_status",
    "reschedule_appointment",
    "mark_reminder_sent",
    # Availability
    "list_available_slots",
    # Sessions
    "create_or_update_session",
    "get_session_by_conversation_id",
    # Logging
    "create_log_entry",
    # Services
    "get_service_by_id",
    "list_active_services",
    # Knowledge base
    "search_knowledge_base",
    "get_message_template",
    # Factory helpers
    "create_redis_client",
    "create_supabase_client",
    "create_supabase_operations",
]
