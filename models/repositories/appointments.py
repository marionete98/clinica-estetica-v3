from __future__ import annotations

import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional
from uuid import UUID

from config.supabase_client import SupabaseClient, get_supabase_client
from models.database import Appointment

from .base import DataRepository
from .contacts import get_contact_repository


class AppointmentRepository(DataRepository):
    """Repository for appointment lifecycle operations."""

    def __init__(self, supabase: SupabaseClient) -> None:
        super().__init__(cache=None)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover - no-op
        return None

    async def close(self) -> None:  # pragma: no cover - managed externally
        return None

    async def create_appointment(
        self,
        appointment_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        def _insert() -> Any:
            return (
                self.supabase.client.table("appointments")
                .insert(appointment_data)
                .execute()
            )

        response = await asyncio.to_thread(_insert)
        return response.data[0]

    async def get_appointment_by_id(
        self, appointment_id: UUID
    ) -> Optional[Dict[str, Any]]:
        def _fetch() -> Any:
            return (
                self.supabase.client.table("appointments")
                .select("*")
                .eq("id", str(appointment_id))
                .execute()
            )

        response = await asyncio.to_thread(_fetch)
        if response.data:
            return response.data[0]
        return None

    async def update_appointment(
        self, appointment_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        def _update() -> Any:
            return (
                self.supabase.client.table("appointments")
                .update(updates)
                .eq("id", str(appointment_id))
                .execute()
            )

        response = await asyncio.to_thread(_update)
        if response.data:
            return response.data[0]
        return None

    async def cancel_appointment(
        self, appointment_id: UUID, reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        update_data = {"status": "cancelled"}
        if reason:
            update_data["cancellation_reason"] = reason
        return await self.update_appointment(appointment_id, update_data)

    async def get_patient_bookings(
        self, contact_id: UUID, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        def _fetch() -> Any:
            query = (
                self.supabase.client.table("appointments")
                .select("*")
                .eq("contact_id", str(contact_id))
            )
            if status:
                query = query.eq("status", status)
            return query.order("start_ts", desc=True).execute()

        response = await asyncio.to_thread(_fetch)
        return response.data or []

    async def list_available_slots(
        self, service_id: UUID, date_range: Dict[str, datetime]
    ) -> List[Dict[str, Any]]:
        def _fetch_slots() -> Any:
            query = (
                self.supabase.client.table("available_slots")
                .select("*")
                .eq("service_id", str(service_id))
            )
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            if start_date:
                query = query.gte("start_ts", start_date.isoformat())
            if end_date:
                query = query.lte("end_ts", end_date.isoformat())
            return query.order("start_ts").execute()

        response = await asyncio.to_thread(_fetch_slots)
        return response.data or []

    async def mark_reminder_sent(
        self, appointment_id: UUID, reminder_type: str
    ) -> Optional[Dict[str, Any]]:
        if reminder_type == "d1":
            update_data = {"reminder_d1_sent": True}
        elif reminder_type == "h2":
            update_data = {"reminder_h2_sent": True}
        else:
            raise ValueError(f"Invalid reminder type: {reminder_type}")
        return await self.update_appointment(appointment_id, update_data)

    async def reschedule_appointment(
        self, appointment_id: UUID, new_start_ts: datetime, new_end_ts: datetime
    ) -> Dict[str, Any]:
        appointment = await self.get_appointment_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        if (appointment.get("reschedule_count") or 0) >= 2:
            raise ValueError("Maximum reschedule limit (2) reached")

        updates = {
            "start_ts": new_start_ts.isoformat(),
            "end_ts": new_end_ts.isoformat(),
            "reschedule_count": (appointment.get("reschedule_count") or 0) + 1,
            "reminder_d1_sent": False,
            "reminder_h2_sent": False,
        }
        updated = await self.update_appointment(appointment_id, updates)
        if not updated:
            raise ValueError("Failed to reschedule appointment")
        return updated

    async def update_status(
        self, appointment_id: UUID, status: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        updated = await self.update_appointment(
            appointment_id,
            {
                "status": status,
                **({"cancellation_reason": reason} if reason else {}),
            },
        )
        if not updated:
            raise ValueError("Failed to update appointment status")

        if status == "no_show":
            await get_contact_repository().increment_no_show_count(
                UUID(updated["contact_id"])
            )
        return updated


@lru_cache
def get_appointment_repository() -> AppointmentRepository:
    return AppointmentRepository(supabase=get_supabase_client())


async def create_appointment(**kwargs: Any) -> Appointment:
    data = await get_appointment_repository().create_appointment(kwargs)
    return Appointment(**data)


async def get_appointment_by_id(appointment_id: UUID) -> Optional[Appointment]:
    data = await get_appointment_repository().get_appointment_by_id(appointment_id)
    return Appointment(**data) if data else None


async def get_appointments_by_contact(
    contact_id: UUID, status: Optional[str] = None
) -> List[Appointment]:
    data = await get_appointment_repository().get_patient_bookings(contact_id, status)
    return [Appointment(**item) for item in data]


async def update_appointment_status(
    appointment_id: UUID, status: str, cancellation_reason: Optional[str] = None
) -> Appointment:
    data = await get_appointment_repository().update_status(
        appointment_id, status, cancellation_reason
    )
    return Appointment(**data)


async def reschedule_appointment(
    appointment_id: UUID, new_start_ts: datetime, new_end_ts: datetime
) -> Appointment:
    data = await get_appointment_repository().reschedule_appointment(
        appointment_id, new_start_ts, new_end_ts
    )
    return Appointment(**data)


async def mark_reminder_sent(appointment_id: UUID, reminder_type: str) -> None:
    await get_appointment_repository().mark_reminder_sent(appointment_id, reminder_type)


__all__ = [
    "AppointmentRepository",
    "get_appointment_repository",
    "create_appointment",
    "get_appointment_by_id",
    "get_appointments_by_contact",
    "update_appointment_status",
    "reschedule_appointment",
    "mark_reminder_sent",
]
