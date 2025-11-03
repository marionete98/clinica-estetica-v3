"""
Scheduling tools for AutoGen agents.
Provides functions for listing available slots, creating bookings, and retrieving patient appointments.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 16.2, 16.3
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, time, timedelta
from uuid import UUID

from config.settings import settings
from tools.calendar_api_client import get_calendar_client, CalendarAPIError
from models.repository import (
    get_contact_by_id,
    get_service_by_id,
    create_appointment as repo_create_appointment
)

logger = logging.getLogger(__name__)


# Business hours configuration
BUSINESS_HOURS = {
    "monday": {"open": True, "start": "08:30", "end": "19:00"},
    "tuesday": {"open": True, "start": "08:30", "end": "19:00"},
    "wednesday": {"open": True, "start": "08:30", "end": "19:00"},
    "thursday": {"open": True, "start": "08:30", "end": "19:00"},
    "friday": {"open": True, "start": "08:30", "end": "19:00"},
    "saturday": {"open": True, "start": "08:30", "end": "12:00"},
    "sunday": {"open": False, "start": None, "end": None}
}


def parse_time(time_str: str) -> time:
    """
    Parse time string in HH:MM format to time object.

    Args:
        time_str: Time string in HH:MM format (e.g., "14:30", "08:00")

    Returns:
        time: Python time object

    Raises:
        ValueError: If time_str is not in valid HH:MM format

    Example:
        >>> t = parse_time("14:30")
        >>> print(t.hour, t.minute)
        14 30
    """
    if not time_str or ':' not in time_str:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")

    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time values: hour={hour}, minute={minute}")
        return time(hour, minute)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Failed to parse time '{time_str}': {e}")


def is_within_business_hours(dt: datetime) -> bool:
    """
    Check if a datetime falls within business hours.
    
    Args:
        dt: Datetime to check
        
    Returns:
        True if within business hours, False otherwise
    """
    weekday = dt.strftime('%A').lower()
    
    if weekday not in BUSINESS_HOURS or not BUSINESS_HOURS[weekday]["open"]:
        return False
    
    day_config = BUSINESS_HOURS[weekday]
    start_time = parse_time(day_config["start"])
    end_time = parse_time(day_config["end"])
    
    return start_time <= dt.time() < end_time


def generate_time_slots(
    start_date: date,
    end_date: date,
    duration_min: int,
    interval_min: int = 30
) -> List[Tuple[datetime, datetime]]:
    """
    Generate all possible time slots within business hours for a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        duration_min: Duration of each slot in minutes
        interval_min: Interval between slot start times (default: 30 minutes)
        
    Returns:
        List of (start_datetime, end_datetime) tuples
    """
    slots = []
    current_date = start_date
    
    while current_date <= end_date:
        weekday = current_date.strftime('%A').lower()
        
        # Skip if not a business day
        if weekday not in BUSINESS_HOURS or not BUSINESS_HOURS[weekday]["open"]:
            current_date += timedelta(days=1)
            continue
        
        # Get business hours for this day
        day_config = BUSINESS_HOURS[weekday]
        start_time = parse_time(day_config["start"])
        end_time = parse_time(day_config["end"])
        
        # Generate slots for the day
        current_time = datetime.combine(current_date, start_time)
        day_end = datetime.combine(current_date, end_time)
        
        while current_time < day_end:
            slot_end = current_time + timedelta(minutes=duration_min)
            
            # Only include slot if it ends before business hours end
            if slot_end.time() <= end_time:
                slots.append((current_time, slot_end))
            
            # Move to next slot
            current_time += timedelta(minutes=interval_min)
        
        current_date += timedelta(days=1)
    
    return slots


async def list_available_slots(
    service_id: str,
    date_range: int = 7,
    start_date: Optional[str] = None,
    max_slots: int = 10
) -> List[Dict[str, Any]]:
    """
    List available time slots for a procedure using Calendar API.
    
    This function:
    1. Fetches existing appointments from Calendar API
    2. Generates potential slots within business hours
    3. Filters out conflicts and slots with insufficient advance time
    4. Adds 10-minute interval between procedures
    5. Limits results to max_slots (default: 10)
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 16.2, 16.3
    
    Args:
        procedure_name: Name of the procedure (e.g., "Botox Facial", "Depilação a Laser")
        duration_min: Duration in minutes (default: 60)
        date_range: Number of days to search (default: 7)
        start_date: Start date for search (YYYY-MM-DD format, default: today)
        max_slots: Maximum number of slots to return (default: 10)
        
    Returns:
        List of available slots:
        [
            {
                "start_datetime": "2025-10-17T14:00:00",
                "end_datetime": "2025-10-17T15:00:00",
                "date": "2025-10-17",
                "start_time": "14:00",
                "end_time": "15:00",
                "duration_min": 60,
                "procedure": "Botox Facial"
            },
            ...
        ]
        
    Raises:
        ValueError: If invalid parameters
        CalendarAPIError: If calendar API fails
    """
    try:
        # Parse start date
        if start_date:
            search_start = datetime.fromisoformat(start_date).date()
        else:
            search_start = date.today()
        
        search_end = search_start + timedelta(days=date_range - 1)
        
        # Retrieve service details (duration, name)
        service = await get_service_by_id(UUID(service_id)) if service_id else None
        if not service:
            raise ValueError(f"Service {service_id} not found")

        duration_min = int(getattr(service, "duration_min", 60) or 60)

        logger.info(
            f"Listing available slots: service_id={service_id}, procedure={getattr(service, 'name', 'N/A')}, "
            f"duration={duration_min}min, date_range={search_start} to {search_end}"
        )
        
        # Get calendar client
        calendar_client = await get_calendar_client()
        
        # Fetch existing appointments from Calendar API
        existing_appointments = await calendar_client.get_appointments(
            start_date=search_start.isoformat(),
            end_date=search_end.isoformat()
        )
        
        # Filter only scheduled appointments
        confirmed_appointments = [
            apt for apt in existing_appointments
            if apt.get('status') == 'scheduled'
        ]
        
        logger.info(
            f"Found {len(confirmed_appointments)} scheduled appointments "
            f"in date range"
        )
        
        # Generate all possible slots
        duration_with_interval = duration_min + 10  # Add 10-minute interval
        all_slots = generate_time_slots(
            search_start,
            search_end,
            duration_with_interval
        )
        
        # Filter slots
        available_slots = []
        now = datetime.now()
        min_advance = now + timedelta(hours=settings.min_booking_advance_hours)
        
        for slot_start, slot_end in all_slots:
            # Check minimum advance time
            if slot_start < min_advance:
                continue
            
            # Check for conflicts with existing appointments
            has_conflict = False
            for apt in confirmed_appointments:
                apt_start = datetime.fromisoformat(
                    f"{apt['appointment_date']}T{apt['start_time']}"
                )
                apt_end = datetime.fromisoformat(
                    f"{apt['appointment_date']}T{apt['end_time']}"
                )
                
                # Check if slots overlap
                if slot_start < apt_end and slot_end > apt_start:
                    has_conflict = True
                    break
            
            if not has_conflict:
                # Adjust end time to actual procedure duration (without interval)
                actual_end = slot_start + timedelta(minutes=duration_min)
                
                slot_info = {
                    "start_datetime": slot_start.isoformat(),
                    "end_datetime": actual_end.isoformat(),
                    "date": slot_start.date().isoformat(),
                    "start_time": slot_start.time().strftime('%H:%M'),
                    "end_time": actual_end.time().strftime('%H:%M'),
                    "duration_min": duration_min,
                    "procedure": getattr(service, "name", "")
                }
                
                available_slots.append(slot_info)
                
                # Limit results to max_slots for better UX
                if len(available_slots) >= max_slots:
                    break
        
        logger.info(
            f"Found {len(available_slots)} available slots for service_id={service_id} "
            f"(limited to {max_slots})"
        )
        
        # Fallback: if no slots and no explicit start_date, try next 3 days
        if not available_slots and start_date is None:
            for offset in range(1, 4):
                day = date.today() + timedelta(days=offset)
                # Skip Sunday
                if day.strftime('%A').lower() == 'sunday':
                    continue
                try:
                    extra_appointments = await calendar_client.get_appointments(
                        start_date=day.isoformat(), end_date=day.isoformat()
                    )
                except CalendarAPIError:
                    extra_appointments = []
                confirmed_appointments = [
                    apt for apt in extra_appointments if apt.get('status') == 'scheduled'
                ]
                all_slots = generate_time_slots(day, day, duration_with_interval)
                for slot_start, slot_end in all_slots:
                    if slot_start < datetime.now() + timedelta(hours=settings.min_booking_advance_hours):
                        continue
                    has_conflict = False
                    for apt in confirmed_appointments:
                        apt_start = datetime.fromisoformat(f"{apt['appointment_date']}T{apt['start_time']}")
                        apt_end = datetime.fromisoformat(f"{apt['appointment_date']}T{apt['end_time']}")
                        if slot_start < apt_end and slot_end > apt_start:
                            has_conflict = True
                            break
                    if not has_conflict:
                        actual_end = slot_start + timedelta(minutes=duration_min)
                        slot_info = {
                            "start_datetime": slot_start.isoformat(),
                            "end_datetime": actual_end.isoformat(),
                            "date": slot_start.date().isoformat(),
                            "start_time": slot_start.time().strftime('%H:%M'),
                            "end_time": actual_end.time().strftime('%H:%M'),
                            "duration_min": duration_min,
                            "procedure": getattr(service, "name", "")
                        }
                        available_slots.append(slot_info)
                        if len(available_slots) >= max_slots:
                            break
                if available_slots:
                    break

        return available_slots
        
    except ValueError as e:
        logger.error(f"Validation error in list_available_slots: {e}")
        raise
    except CalendarAPIError as e:
        logger.error(f"Calendar API error in list_available_slots: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_available_slots: {e}")
        raise


async def create_booking(
    contact_id: str,
    service_id: str,
    start_datetime: str,
    room: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new booking/appointment using Calendar API.
    
    This function:
    1. Validates minimum advance time (1 hour)
    2. Retrieves contact details from our database
    3. Creates appointment via Calendar API
    4. Stores tracking record in our database
    
    Requirements: 2.6, 2.7, 3.1, 3.2, 3.3
    
    Args:
        contact_id: Contact UUID
        procedure_name: Name of procedure (e.g., "Botox Facial")
        treatment_category: Treatment category (e.g., "Harmonização facial")
        duration_min: Duration in minutes
        start_datetime: Start datetime (ISO format: YYYY-MM-DDTHH:MM:SS)
        room: Room name (optional, e.g., "Sala 02")
        conversation_id: Chatwoot conversation ID (optional)
        
    Returns:
        Dictionary with booking information:
        {
            "booking_id": "uuid",
            "calendar_appointment_id": "string",
            "contact_id": "uuid",
            "start_datetime": "2025-10-17T14:00:00",
            "end_datetime": "2025-10-17T15:00:00",
            "status": "scheduled",
            "client_name": "João Silva",
            "client_phone": "+5511999999999",
            "procedure": "Botox Facial",
            "treatment": "Harmonização facial",
            "room": "Sala 02"
        }
        
    Raises:
        ValueError: If validation fails or contact not found
        CalendarAPIError: If calendar API fails
    """
    try:
        # Parse start datetime
        start_dt = datetime.fromisoformat(start_datetime)
        
        logger.info(
            f"Creating booking: contact_id={contact_id}, service_id={service_id}, "
            f"start_datetime={start_datetime}"
        )
        
        # Validate minimum advance time
        now = datetime.now()
        min_advance = now + timedelta(hours=settings.min_booking_advance_hours)
        
        if start_dt < min_advance:
            raise ValueError(
                f"Booking must be at least {settings.min_booking_advance_hours} "
                f"hour(s) in advance. Requested: {start_datetime}, "
                f"Minimum: {min_advance.isoformat()}"
            )
        
        # Validate business hours
        if not is_within_business_hours(start_dt):
            raise ValueError(
                f"Requested time {start_datetime} is outside business hours"
            )
        
        # Get contact details and service details
        contact = await get_contact_by_id(UUID(contact_id))
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        service = await get_service_by_id(UUID(service_id))
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        # Calculate end datetime
        duration_min = int(getattr(service, "duration_min", 60) or 60)
        end_dt = start_dt + timedelta(minutes=duration_min)
        
        # Prepare appointment data for Calendar API
        appointment_data = {
            "client_name": contact.name or "Cliente",
            "client_phone": contact.phone,
            "client_email": contact.email or "",
            "appointment_date": start_dt.date().isoformat(),
            "start_time": start_dt.time().strftime('%H:%M'),
            "end_time": end_dt.time().strftime('%H:%M'),
            "duration": f"{duration_min}min",
            "procedure": getattr(service, "name", ""),
            "treatment": getattr(service, "category", ""),
            "room": room or "A definir",
            "observations": f"Agendado via WhatsApp. Conversation ID: {conversation_id or 'N/A'}",
            "status": "scheduled"
        }
        
        # Create appointment via calendar API
        calendar_client = await get_calendar_client()
        calendar_appointment = await calendar_client.create_appointment(appointment_data)
        
        # Note: Calendar API is the source of truth for appointments
        # Internal tracking is disabled since we're using Calendar API
        # The calendar_appointment_id is the primary identifier
        our_appointment_id = calendar_appointment.get('id')
        
        logger.info(
            f"Created booking: calendar_id={calendar_appointment.get('id')}, "
            f"our_id={our_appointment_id}"
        )
        
        # Prepare response
        result = {
            "booking_id": our_appointment_id,
            "calendar_appointment_id": calendar_appointment.get('id'),
            "contact_id": str(contact.id),
            "start_datetime": start_dt.isoformat(),
            "end_datetime": end_dt.isoformat(),
            "status": "scheduled",
            "client_name": contact.name,
            "client_phone": contact.phone,
            "procedure": getattr(service, "name", ""),
            "treatment": getattr(service, "category", ""),
            "room": room or "A definir",
            "conversation_id": conversation_id
        }
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in create_booking: {e}")
        raise
    except CalendarAPIError as e:
        logger.error(f"Calendar API error in create_booking: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_booking: {e}")
        raise


async def get_patient_bookings(phone: str) -> List[Dict[str, Any]]:
    """
    Get all bookings for a patient by phone number.
    
    This function queries the calendar API for appointments matching
    the patient's phone number.
    
    Requirements: 3.3
    
    Args:
        phone: Patient's phone number
        
    Returns:
        List of booking dictionaries:
        [
            {
                "id": "uuid",
                "client_name": "João Silva",
                "client_phone": "+5511999999999",
                "appointment_date": "2025-10-17",
                "start_time": "14:00",
                "end_time": "15:00",
                "procedure": "Botox",
                "treatment": "Harmonização facial",
                "room": "Sala 02",
                "status": "scheduled",
                "created_at": "2025-10-16T10:00:00Z"
            },
            ...
        ]
        
    Raises:
        CalendarAPIError: If calendar API fails
    """
    try:
        logger.info(f"Retrieving bookings for phone: {phone}")
        
        # Get calendar client
        calendar_client = await get_calendar_client()
        
        # Fetch all appointments (we'll filter by phone)
        # Note: Calendar API doesn't support phone filter, so we fetch recent appointments
        today = date.today()
        future_date = today + timedelta(days=90)  # Next 3 months
        
        all_appointments = await calendar_client.get_appointments(
            start_date=today.isoformat(),
            end_date=future_date.isoformat()
        )
        
        # Filter by phone
        patient_appointments = [
            apt for apt in all_appointments
            if apt.get('client_phone') == phone
        ]
        
        logger.info(
            f"Found {len(patient_appointments)} bookings for phone: {phone}"
        )
        
        return patient_appointments
        
    except CalendarAPIError as e:
        logger.error(f"Calendar API error in get_patient_bookings: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_patient_bookings: {e}")
        raise


# Tool metadata for AutoGen registration
SCHEDULER_TOOLS = {
    "list_available_slots": {
        "function": list_available_slots,
        "description": (
            "List available time slots for a procedure. "
            "Use this when a patient wants to see available appointment times. "
            "Respects business hours, minimum advance time (1 hour), and existing bookings."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "string",
                    "description": "Service UUID (determines procedure name and duration)"
                },
                "date_range": {
                    "type": "integer",
                    "description": "Number of days to search (default: 7)",
                    "default": 7
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for search (YYYY-MM-DD format, default: today)"
                },
                "max_slots": {
                    "type": "integer",
                    "description": "Maximum number of slots to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["service_id"]
        }
    },
    "create_booking": {
        "function": create_booking,
        "description": (
            "Create a new appointment booking. "
            "Use this after the patient confirms a specific time slot. "
            "Always request explicit confirmation before calling this function."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "Contact UUID"
                },
                "service_id": {
                    "type": "string",
                    "description": "Service UUID (determines procedure name, category and duration)"
                },
                "start_datetime": {
                    "type": "string",
                    "description": "Start datetime (ISO format: YYYY-MM-DDTHH:MM:SS)"
                },
                "room": {
                    "type": "string",
                    "description": "Room name (optional, e.g., 'Sala 02')"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Chatwoot conversation ID (optional)"
                }
            },
            "required": ["contact_id", "service_id", "start_datetime"]
        }
    },
    "get_patient_bookings": {
        "function": get_patient_bookings,
        "description": (
            "Get all bookings for a patient by phone number. "
            "Use this when a patient wants to see their existing appointments "
            "or when checking for conflicts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Patient's phone number"
                }
            },
            "required": ["phone"]
        }
    }
}

