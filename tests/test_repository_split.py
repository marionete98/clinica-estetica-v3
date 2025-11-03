import os

import pytest

_REQUIRED_ENV = {
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_KEY": "test-supabase-key",
    "REDIS_URL": "redis://localhost:6379/0",
    "CHATWOOT_API_URL": "https://chatwoot.example.com",
    "CHATWOOT_ACCOUNT_ID": "1",
    "CHATWOOT_API_TOKEN": "test-chatwoot-token",
}

for _env_key, _env_value in _REQUIRED_ENV.items():
    os.environ.setdefault(_env_key, _env_value)

import models.repository as legacy_repo
from config.redis_client import redis_client as redis_from_config
from config.supabase_client import supabase_client as supabase_from_config
from config.supabase_client import supabase_ops as supabase_ops_from_config
from models.repositories import appointments, availability, contacts, knowledge_base, logs, services, sessions


@pytest.mark.parametrize(
    ("legacy", "modern"),
    [
        (legacy_repo.create_or_update_contact, contacts.create_or_update_contact),
        (legacy_repo.get_contact_by_phone, contacts.get_contact_by_phone),
        (legacy_repo.get_contact_by_id, contacts.get_contact_by_id),
        (legacy_repo.increment_no_show_count, contacts.increment_no_show_count),
        (legacy_repo.create_appointment, appointments.create_appointment),
        (legacy_repo.get_appointment_by_id, appointments.get_appointment_by_id),
        (legacy_repo.get_appointments_by_contact, appointments.get_appointments_by_contact),
        (legacy_repo.update_appointment_status, appointments.update_appointment_status),
        (legacy_repo.reschedule_appointment, appointments.reschedule_appointment),
        (legacy_repo.mark_reminder_sent, appointments.mark_reminder_sent),
        (legacy_repo.list_available_slots, availability.list_available_slots),
        (legacy_repo.create_or_update_session, sessions.create_or_update_session),
        (legacy_repo.get_session_by_conversation_id, sessions.get_session_by_conversation_id),
        (legacy_repo.create_log_entry, logs.create_log_entry),
        (legacy_repo.get_service_by_id, services.get_service_by_id),
        (legacy_repo.list_active_services, services.list_active_services),
        (legacy_repo.search_knowledge_base, knowledge_base.search_knowledge_base),
        (legacy_repo.get_message_template, knowledge_base.get_message_template),
    ],
)
def test_legacy_repository_reexports_domain_functions(legacy, modern):
    assert legacy is modern


def test_repository_module_exposes_injected_clients():
    assert legacy_repo.redis_client is redis_from_config
    assert legacy_repo.supabase_client is supabase_from_config
    assert legacy_repo.supabase_ops is supabase_ops_from_config
