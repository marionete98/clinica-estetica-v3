"""
Availability calculations for appointment slots.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List
from uuid import UUID

from config.supabase_client import supabase_client
from models.database import Appointment, Service


async def list_available_slots(
    service_id: UUID, start_date: date, end_date: date, business_hours: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    List available time slots for a service within a date range.
    """
    supabase = supabase_client.client

    service_response = (
        supabase.table("services").select("*").eq("id", str(service_id)).execute()
    )
    if not service_response.data:
        raise ValueError(f"Service {service_id} not found")

    service = Service(**service_response.data[0])

    appointments_response = (
        supabase.table("appointments")
        .select("*")
        .gte("start_ts", start_date.isoformat())
        .lte("start_ts", end_date.isoformat())
        .eq("status", "confirmed")
        .execute()
    )

    existing_appointments = [Appointment(**apt) for apt in appointments_response.data]

    available_slots: List[Dict[str, Any]] = []
    current_date = start_date

    while current_date <= end_date:
        weekday = current_date.strftime("%A").lower()
        day_config = business_hours.get(weekday, {})
        if not day_config.get("open", False):
            current_date += timedelta(days=1)
            continue

        start_time_str = day_config.get("start", "09:00")
        end_time_str = day_config.get("end", "18:00")

        start_hour, start_min = map(int, start_time_str.split(":"))
        end_hour, end_min = map(int, end_time_str.split(":"))

        current_time = time(start_hour, start_min)
        closing_time = time(end_hour, end_min)

        while current_time < closing_time:
            slot_start = datetime.combine(current_date, current_time)
            slot_end = slot_start + timedelta(minutes=service.duration_min)

            is_available = True
            for apt in existing_appointments:
                if slot_start < apt.end_ts and slot_end > apt.start_ts:
                    is_available = False
                    break

            if is_available and slot_end.time() <= closing_time:
                available_slots.append(
                    {
                        "date": current_date.isoformat(),
                        "start_time": current_time.strftime("%H:%M"),
                        "end_time": slot_end.time().strftime("%H:%M"),
                        "start_ts": slot_start.isoformat(),
                        "end_ts": slot_end.isoformat(),
                    }
                )

            current_time = (
                datetime.combine(current_date, current_time) + timedelta(minutes=30)
            ).time()

        current_date += timedelta(days=1)

    return available_slots


__all__ = ["list_available_slots"]
