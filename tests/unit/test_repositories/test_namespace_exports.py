"""Ensure the consolidated repositories namespace re-exports domain helpers."""

from __future__ import annotations

import importlib

import pytest

import models.repositories as repositories


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        ("create_or_update_contact", "models.repositories.contacts"),
        ("get_contact_by_phone", "models.repositories.contacts"),
        ("get_contact_by_id", "models.repositories.contacts"),
        ("increment_no_show_count", "models.repositories.contacts"),
        ("create_appointment", "models.repositories.appointments"),
        ("get_appointment_by_id", "models.repositories.appointments"),
        ("get_appointments_by_contact", "models.repositories.appointments"),
        ("update_appointment_status", "models.repositories.appointments"),
        ("reschedule_appointment", "models.repositories.appointments"),
        ("mark_reminder_sent", "models.repositories.appointments"),
        ("list_available_slots", "models.repositories.availability"),
        ("search_knowledge_base", "models.repositories.knowledge_base"),
        ("get_message_template", "models.repositories.knowledge_base"),
        ("create_or_update_session", "models.repositories.sessions"),
        ("get_session_by_conversation_id", "models.repositories.sessions"),
        ("get_service_by_id", "models.repositories.services"),
        ("list_active_services", "models.repositories.services"),
        ("create_log_entry", "models.repositories.logs"),
    ],
)
def test_namespace_reexports(attribute: str, expected: str) -> None:
    value = getattr(repositories, attribute)
    module = importlib.import_module(expected)
    assert value is getattr(module, attribute)
