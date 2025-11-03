"""Unit tests for the appointment repository."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict
from uuid import uuid4

import pytest

from models.repositories.appointments import AppointmentRepository

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> AppointmentRepository:
    return AppointmentRepository(supabase=fake_supabase)


@pytest.mark.asyncio
async def test_create_appointment_persists_payload(repository: AppointmentRepository, fake_supabase: FakeSupabase) -> None:
    payload: Dict[str, str] = {"contact_id": "123", "service_id": "456"}

    result = await repository.create_appointment(payload)

    assert result["contact_id"] == "123"
    # Fake query adds generated id automatically
    assert result["id"] == "generated-id"
    assert fake_supabase.client.table_calls == ["appointments"]


@pytest.mark.asyncio
async def test_get_appointment_by_id_returns_first_match(repository: AppointmentRepository, fake_supabase: FakeSupabase) -> None:
    appointment_id = uuid4()
    query = fake_supabase.client.table("appointments")
    query._data = {"id": str(appointment_id), "status": "confirmed"}

    result = await repository.get_appointment_by_id(appointment_id)

    assert result == query._data


@pytest.mark.asyncio
async def test_cancel_appointment_updates_status(repository: AppointmentRepository, fake_supabase: FakeSupabase) -> None:
    appointment_id = uuid4()
    query = fake_supabase.client.table("appointments")
    query._data = {"id": str(appointment_id), "status": "confirmed"}

    updated = await repository.cancel_appointment(appointment_id, reason="client_request")

    assert updated["status"] == "cancelled"
    assert query.history[-1] == (
        "update",
        {"status": "cancelled", "cancellation_reason": "client_request"},
    )


@pytest.mark.asyncio
async def test_list_available_slots_filters_by_range(repository: AppointmentRepository, fake_supabase: FakeSupabase) -> None:
    service_id = uuid4()
    query = fake_supabase.client.table("available_slots")
    query._data = [
        {
            "service_id": str(service_id),
            "start_ts": "2024-06-01T10:00:00",
            "end_ts": "2024-06-01T10:30:00",
        }
    ]

    slots = await repository.list_available_slots(
        service_id,
        {"start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(days=1)},
    )

    assert len(slots) == 1
    assert slots[0]["service_id"] == str(service_id)
