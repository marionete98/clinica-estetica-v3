"""
Appointment repository operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from config.supabase_client import supabase_client
from models.database import Appointment

from .contacts import increment_no_show_count


async def create_appointment(
    contact_id: UUID,
    service_id: Optional[UUID] = None,
    start_ts: datetime | None = None,
    end_ts: datetime | None = None,
    conversation_id: Optional[str] = None,
    room_id: Optional[UUID] = None,
    equipment_id: Optional[UUID] = None,
) -> Appointment:
    """
    Create a new appointment for internal tracking.
    """
    if start_ts is None or end_ts is None:
        raise ValueError("start_ts and end_ts are required")

    supabase = supabase_client.client

    appointment_data = {
        "contact_id": str(contact_id),
        "service_id": str(service_id) if service_id else None,
        "start_ts": start_ts.isoformat(),
        "end_ts": end_ts.isoformat(),
        "conversation_id": conversation_id,
        "room_id": str(room_id) if room_id else None,
        "equipment_id": str(equipment_id) if equipment_id else None,
        "status": "confirmed",
    }

    response = supabase.table("appointments").insert(appointment_data).execute()
    return Appointment(**response.data[0])


async def get_appointment_by_id(appointment_id: UUID) -> Optional[Appointment]:
    """
    Retrieve appointment by ID.
    """
    supabase = supabase_client.client

    response = (
        supabase.table("appointments")
        .select("*")
        .eq("id", str(appointment_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        return Appointment(**response.data[0])
    return None


async def get_appointments_by_contact(
    contact_id: UUID, status: Optional[str] = None
) -> List[Appointment]:
    """
    Retrieve all appointments for a contact.
    """
    supabase = supabase_client.client

    query = supabase.table("appointments").select("*").eq("contact_id", str(contact_id))

    if status:
        query = query.eq("status", status)

    response = query.order("start_ts", desc=True).execute()

    return [Appointment(**apt) for apt in response.data]


async def update_appointment_status(
    appointment_id: UUID, status: str, cancellation_reason: Optional[str] = None
) -> Appointment:
    """
    Update appointment status.
    """
    supabase = supabase_client.client

    update_data = {"status": status}
    if cancellation_reason:
        update_data["cancellation_reason"] = cancellation_reason

    response = (
        supabase.table("appointments")
        .update(update_data)
        .eq("id", str(appointment_id))
        .execute()
    )

    if status == "no_show":
        appointment = Appointment(**response.data[0])
        await increment_no_show_count(appointment.contact_id)

    return Appointment(**response.data[0])


async def reschedule_appointment(
    appointment_id: UUID, new_start_ts: datetime, new_end_ts: datetime
) -> Appointment:
    """
    Reschedule an appointment to a new time.
    """
    supabase = supabase_client.client

    appointment = await get_appointment_by_id(appointment_id)
    if not appointment:
        raise ValueError(f"Appointment {appointment_id} not found")

    if appointment.reschedule_count >= 2:
        raise ValueError("Maximum reschedule limit (2) reached")

    update_data = {
        "start_ts": new_start_ts.isoformat(),
        "end_ts": new_end_ts.isoformat(),
        "reschedule_count": appointment.reschedule_count + 1,
        "reminder_d1_sent": False,
        "reminder_h2_sent": False,
    }

    response = (
        supabase.table("appointments")
        .update(update_data)
        .eq("id", str(appointment_id))
        .execute()
    )
    return Appointment(**response.data[0])


async def mark_reminder_sent(appointment_id: UUID, reminder_type: str) -> None:
    """
    Mark reminder as sent for an appointment.
    """
    supabase = supabase_client.client

    if reminder_type == "d1":
        update_data = {"reminder_d1_sent": True}
    elif reminder_type == "h2":
        update_data = {"reminder_h2_sent": True}
    else:
        raise ValueError(f"Invalid reminder type: {reminder_type}")

    supabase.table("appointments").update(update_data).eq(
        "id", str(appointment_id)
    ).execute()


__all__ = [
    "create_appointment",
    "get_appointment_by_id",
    "get_appointments_by_contact",
    "update_appointment_status",
    "reschedule_appointment",
    "mark_reminder_sent",
]
