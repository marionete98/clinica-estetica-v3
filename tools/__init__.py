"""
Tools module for AutoGen agents.
Provides functions for contact management, knowledge base search,
scheduling, and rescheduling operations.
"""

from tools.calendar_api_client import (
    CalendarAPIClient,
    CalendarAPIError,
    get_calendar_client,
    close_calendar_client
)

from tools.contact_tools import (
    create_or_update_contact,
    get_contact_by_phone,
    validate_brazilian_phone,
    normalize_brazilian_phone,
    CONTACT_TOOLS
)

from tools.kb_tools import (
    search_knowledge_base,
    get_message_template,
    list_available_templates,
    format_template,
    KB_TOOLS
)

from tools.scheduler_tools import (
    list_available_slots,
    create_booking,
    get_patient_bookings,
    SCHEDULER_TOOLS
)

from tools.reschedule_tools import (
    cancel_booking,
    reschedule_booking,
    check_cancellation_policy,
    RESCHEDULE_TOOLS
)

# Consolidated tool registry for AutoGen
ALL_TOOLS = {
    **CONTACT_TOOLS,
    **KB_TOOLS,
    **SCHEDULER_TOOLS,
    **RESCHEDULE_TOOLS
}

__all__ = [
    # Calendar API Client
    "CalendarAPIClient",
    "CalendarAPIError",
    "get_calendar_client",
    "close_calendar_client",
    
    # Contact Tools
    "create_or_update_contact",
    "get_contact_by_phone",
    "validate_brazilian_phone",
    "normalize_brazilian_phone",
    "CONTACT_TOOLS",
    
    # Knowledge Base Tools
    "search_knowledge_base",
    "get_message_template",
    "list_available_templates",
    "format_template",
    "KB_TOOLS",
    
    # Scheduler Tools
    "list_available_slots",
    "create_booking",
    "get_patient_bookings",
    "SCHEDULER_TOOLS",
    
    # Reschedule Tools
    "cancel_booking",
    "reschedule_booking",
    "check_cancellation_policy",
    "RESCHEDULE_TOOLS",
    
    # All Tools Registry
    "ALL_TOOLS"
]
