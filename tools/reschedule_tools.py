"""
Rescheduling and cancellation tools for AutoGen agents.
Provides functions for canceling and rescheduling appointments with policy validation.
Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from config.settings import settings
from tools.calendar_api_client import get_calendar_client, CalendarAPIError
from models.repositories.appointments import (
    get_appointment_by_id,
    reschedule_appointment as repo_reschedule_appointment,
    update_appointment_status,
)
from models.repositories.contacts import get_contact_by_id
from models.repositories.services import get_service_by_id

logger = logging.getLogger(__name__)


def _now_matching(reference: datetime) -> datetime:
    """Return current time matching timezone awareness of reference datetime."""
    try:
        if reference is None or reference.tzinfo is None or reference.tzinfo.utcoffset(reference) is None:
            return datetime.now()
        return datetime.now(tz=reference.tzinfo)
    except Exception:
        return datetime.now()

async def get_cancellation_policy_hours(service_id: UUID) -> int:
    """
    Get cancellation policy hours for a service based on category.

    This function determines the minimum advance notice required for
    cancellation based on the service category. Different procedures
    have different cancellation policies:

    - Harmonization procedures (Botox, fillers): 4 hours (default from settings)
    - Laser procedures (hair removal): 24 hours (default from settings)
    - Other procedures: Uses harmonization policy (more restrictive)

    The function first checks if the service has a specific cancellation
    policy defined, otherwise falls back to category-based defaults.

    Args:
        service_id: Service UUID from database

    Returns:
        int: Minimum hours required for cancellation (e.g., 4, 24)

    Example:
        >>> policy_hours = await get_cancellation_policy_hours(service_uuid)
        >>> print(f"Must cancel {policy_hours} hours in advance")

    Raises:
        ValueError: If service not found in database
        TypeError: If service_id is not a valid UUID

    Note:
        - Policy hours are configured in settings.py
        - Default harmonization_cancel_hours = 4
        - Default laser_cancel_hours = 24
    """
    if not isinstance(service_id, UUID):
        raise TypeError(f"service_id must be UUID, got {type(service_id)}")

    service = await get_service_by_id(service_id)
    if not service:
        raise ValueError(f"Service {service_id} not found")
    
    # Check if service has specific cancellation policy (coerce to int)
    try:
        custom_hours = getattr(service, 'cancellation_hours', None)
        if custom_hours is not None:
            hours_val = int(custom_hours)
            if hours_val > 0:
                return hours_val
    except Exception:
        pass
    
    # Default policies by service attributes (category/name)
    category_lower = (getattr(service, "category", "") or "").lower()
    name_lower = (getattr(service, "name", "") or "").lower()
    text = f"{category_lower} {name_lower}"

    if ("harmonização" in text) or ("harmonizacao" in text):
        return settings.harmonization_cancel_hours
    if ("laser" in text) or ("depilação" in text) or ("depilacao" in text):
        return settings.laser_cancel_hours
    # Default to harmonization policy (more restrictive)
    return settings.harmonization_cancel_hours


async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an appointment booking.
    
    This function:
    1. Retrieves the appointment from our database
    2. Validates cancellation policy (4h for harmonization, 24h for laser)
    3. Updates status via calendar API (soft delete)
    4. Updates our tracking record
    5. Returns policy violation information if applicable
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    
    Args:
        booking_id: Appointment UUID (from our database)
        reason: Cancellation reason (optional)
        
    Returns:
        Dictionary with cancellation result:
        {
            "success": true,
            "booking_id": "uuid",
            "calendar_appointment_id": "uuid",
            "status": "cancelled",
            "policy_compliant": true,
            "hours_before": 48,
            "required_hours": 24,
            "message": "Appointment cancelled successfully",
            "will_count_as_done": false
        }
        
        If policy violated:
        {
            "success": false,
            "booking_id": "uuid",
            "policy_compliant": false,
            "hours_before": 2,
            "required_hours": 24,
            "message": "Cancellation outside policy window. Session will be counted as done.",
            "will_count_as_done": true
        }
        
    Raises:
        ValueError: If booking not found
        CalendarAPIError: If calendar API fails
    """
    try:
        logger.info(f"Cancelling booking: booking_id={booking_id}, reason={reason}")
        
        # Get appointment from our database
        appointment = await get_appointment_by_id(UUID(booking_id))
        if not appointment:
            raise ValueError(f"Booking {booking_id} not found")
        
        # Check if already cancelled
        if appointment.status == 'cancelled':
            return {
                "success": True,
                "booking_id": booking_id,
                "status": "cancelled",
                "message": "Appointment was already cancelled",
                "policy_compliant": True,
                "will_count_as_done": False
            }
        
        # Get service to check cancellation policy
        service = await get_service_by_id(appointment.service_id)
        if not service:
            raise ValueError(f"Service {appointment.service_id} not found")
        
        # Get cancellation policy hours (robust: infer from multiple cues)
        required_candidates = []
        required_hours_raw = await get_cancellation_policy_hours(appointment.service_id)
        try:
            val = int(required_hours_raw)
            if val > 0:
                required_candidates.append(val)
        except Exception:
            pass
        txt = f"{getattr(service, 'category', '')} {getattr(service, 'name', '')}".lower()
        if ("laser" in txt) or ("depilação" in txt) or ("depilacao" in txt):
            required_candidates.append(settings.laser_cancel_hours)
        else:
            required_candidates.append(settings.harmonization_cancel_hours)
        required_hours = max(required_candidates) if required_candidates else settings.harmonization_cancel_hours
        
        # Calculate hours before appointment (match tz awareness)
        now = _now_matching(appointment.start_ts)
        hours_before = (appointment.start_ts - now).total_seconds() / 3600

        # Enforce policy by service type using configured thresholds
        service_txt = f"{getattr(service, 'category', '')} {getattr(service, 'name', '')}".lower()
        laser_like = ("laser" in service_txt) or ("depilação" in service_txt) or ("depilacao" in service_txt)
        threshold = settings.laser_cancel_hours if laser_like else settings.harmonization_cancel_hours
        if hours_before < float(threshold):
            policy_compliant = False
        else:
            policy_compliant = True
        
        # Check if cancellation is within policy
        try:
            policy_compliant = hours_before >= float(required_hours)
        except Exception:
            policy_compliant = False
        
        if not policy_compliant:
            # Policy violation - session will count as done
            logger.warning(
                f"Cancellation policy violation: booking_id={booking_id}, "
                f"hours_before={hours_before:.1f}, required={required_hours}"
            )
            
            # Update status to no_show in our database
            # This will automatically increment the contact's no_show_count
            # via the update_appointment_status function in repository
            await update_appointment_status(
                appointment.id,
                status='no_show',
                cancellation_reason=f"Late cancellation: {reason or 'No reason provided'}"
            )
            
            return {
                "success": False,
                "booking_id": booking_id,
                "policy_compliant": False,
                "hours_before": round(hours_before, 1),
                "required_hours": required_hours,
                "message": (
                    f"Cancelamento fora do prazo permitido. "
                    f"Para {service.name}, é necessário cancelar com {required_hours}h de antecedência. "
                    f"A sessão será registrada como realizada conforme política da clínica."
                ),
                "will_count_as_done": True,
                "service_name": service.name
            }
        
        # Policy compliant - proceed with cancellation
        # Get calendar client
        try:
            calendar_client = await get_calendar_client()
        except CalendarAPIError:
            calendar_client = None
        
        # Find calendar appointment ID
        # We need to search by our tracking data
        # For now, we'll use the observations field which contains our conversation_id
        # In production, we should store calendar_appointment_id in our database
        
        # Search for appointment in calendar API
        appointments = await calendar_client.get_appointments(
            date=appointment.start_ts.date().isoformat()
        )
        
        calendar_appointment_id = None
        for apt in appointments:
            apt_start = datetime.fromisoformat(
                f"{apt['appointment_date']}T{apt['start_time']}"
            )
            # Match by time and procedure
            if (apt_start == appointment.start_ts and 
                apt.get('procedure') == service.name):
                calendar_appointment_id = apt['id']
                break
        
        if calendar_appointment_id:
            # Cancel via calendar API (soft delete)
            await calendar_client.delete_appointment(calendar_appointment_id)
            logger.info(f"Cancelled calendar appointment: {calendar_appointment_id}")
        else:
            logger.warning(
                f"Could not find calendar appointment for booking {booking_id}"
            )
        
        # Update our database
        await update_appointment_status(
            appointment.id,
            status='cancelled',
            cancellation_reason=reason
        )
        
        logger.info(f"Successfully cancelled booking: {booking_id}")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "calendar_appointment_id": calendar_appointment_id,
            "status": "cancelled",
            "policy_compliant": True,
            "hours_before": round(hours_before, 1),
            "required_hours": required_hours,
            "message": "Agendamento cancelado com sucesso",
            "will_count_as_done": False,
            "service_name": service.name
        }
        
    except ValueError as e:
        logger.error(f"Validation error in cancel_booking: {e}")
        raise
    except CalendarAPIError as e:
        logger.error(f"Calendar API error in cancel_booking: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cancel_booking: {e}")
        raise


async def reschedule_booking(
    booking_id: str,
    new_start_datetime: str
) -> Dict[str, Any]:
    """
    Reschedule an appointment to a new time.
    
    This function:
    1. Retrieves the appointment from our database
    2. Checks reschedule limit (maximum 2 reschedules)
    3. Validates cancellation policy for the current time
    4. Validates new time (business hours, advance time)
    5. Updates appointment via calendar API
    6. Updates our tracking record
    
    Requirements: 4.5, 4.6, 4.7, 4.8
    
    Args:
        booking_id: Appointment UUID (from our database)
        new_start_datetime: New start datetime (ISO format: YYYY-MM-DDTHH:MM:SS)
        
    Returns:
        Dictionary with reschedule result:
        {
            "success": true,
            "booking_id": "uuid",
            "calendar_appointment_id": "uuid",
            "old_start_datetime": "2025-10-17T14:00:00",
            "new_start_datetime": "2025-10-18T15:00:00",
            "reschedule_count": 1,
            "remaining_reschedules": 1,
            "message": "Appointment rescheduled successfully"
        }
        
        If limit exceeded:
        {
            "success": false,
            "booking_id": "uuid",
            "reschedule_count": 2,
            "remaining_reschedules": 0,
            "message": "Maximum reschedule limit (2) reached. Please contact clinic for assistance."
        }
        
    Raises:
        ValueError: If validation fails or booking not found
        CalendarAPIError: If calendar API fails
    """
    try:
        # Parse new start datetime
        new_start_dt = datetime.fromisoformat(new_start_datetime)
        
        logger.info(
            f"Rescheduling booking: booking_id={booking_id}, "
            f"new_start_datetime={new_start_datetime}"
        )
        
        # Get appointment from our database
        appointment = await get_appointment_by_id(UUID(booking_id))
        if not appointment:
            raise ValueError(f"Booking {booking_id} not found")
        
        # Check reschedule limit
        if appointment.reschedule_count >= settings.max_reschedule_count:
            logger.warning(
                f"Reschedule limit exceeded: booking_id={booking_id}, "
                f"count={appointment.reschedule_count}"
            )
            
            return {
                "success": False,
                "booking_id": booking_id,
                "reschedule_count": appointment.reschedule_count,
                "remaining_reschedules": 0,
                "message": (
                    f"Limite de remarcações atingido ({settings.max_reschedule_count}). "
                    f"Por favor, entre em contato com a clínica para assistência."
                )
            }
        
        # Get service details
        service = await get_service_by_id(appointment.service_id)
        if not service:
            raise ValueError(f"Service {appointment.service_id} not found")
        
        # Validate cancellation policy for current appointment (robust)
        required_candidates = []
        required_hours_raw = await get_cancellation_policy_hours(appointment.service_id)
        try:
            val = int(required_hours_raw)
            if val > 0:
                required_candidates.append(val)
        except Exception:
            pass
        txt = f"{getattr(service, 'category', '')} {getattr(service, 'name', '')}".lower()
        if ("laser" in txt) or ("depilação" in txt) or ("depilacao" in txt):
            required_candidates.append(settings.laser_cancel_hours)
        else:
            required_candidates.append(settings.harmonization_cancel_hours)
        required_hours = max(required_candidates) if required_candidates else settings.harmonization_cancel_hours
        # Use matching tz awareness
        now = _now_matching(appointment.start_ts)
        hours_before = (appointment.start_ts - now).total_seconds() / 3600

        # Enforce policy by service type using configured thresholds
        service_txt = f"{getattr(service, 'category', '')} {getattr(service, 'name', '')}".lower()
        laser_like = ("laser" in service_txt) or ("depilação" in service_txt) or ("depilacao" in service_txt)
        base_threshold = settings.laser_cancel_hours if laser_like else settings.harmonization_cancel_hours
        if hours_before < float(base_threshold):
            needs_handover = True
        else:
            needs_handover = False
        
        try:
            needs_handover = float(hours_before) < float(required_hours)
        except Exception:
            needs_handover = True
        if needs_handover:
            return {
                "success": False,
                "booking_id": booking_id,
                "message": (
                    f"Não é possível remarcar. Para {service.name}, é necessário "
                    f"remarcar com {required_hours}h de antecedência. "
                    f"Por favor, entre em contato com a clínica."
                ),
                "policy_compliant": False,
                "hours_before": round(hours_before, 1),
                "required_hours": required_hours
            }
        
        # Validate new time - minimum advance
        min_advance = now + timedelta(hours=settings.min_booking_advance_hours)
        if new_start_dt < min_advance:
            raise ValueError(
                f"New appointment time must be at least "
                f"{settings.min_booking_advance_hours} hour(s) in advance"
            )
        
        # Validate business hours
        from tools.scheduler_tools import is_within_business_hours
        if not is_within_business_hours(new_start_dt):
            raise ValueError(
                f"New time {new_start_datetime} is outside business hours"
            )
        
        # Calculate new end datetime (default to 60 minutes if missing)
        duration_raw = getattr(service, "duration_min", 60)
        try:
            duration_min = int(duration_raw) if duration_raw is not None else 60
        except Exception:
            duration_min = 60
        new_end_dt = new_start_dt + timedelta(minutes=duration_min)
        
        # Get calendar client
        calendar_client = await get_calendar_client()
        
        # Find calendar appointment ID
        try:
            if calendar_client is not None:
                appointments = await calendar_client.get_appointments(
                    date=appointment.start_ts.date().isoformat()
                )
            else:
                appointments = []
        except CalendarAPIError:
            appointments = []
        
        calendar_appointment_id = None
        for apt in appointments:
            apt_start = datetime.fromisoformat(
                f"{apt['appointment_date']}T{apt['start_time']}"
            )
            if (apt_start == appointment.start_ts and 
                apt.get('procedure') == service.name):
                calendar_appointment_id = apt['id']
                break
        
        if not calendar_appointment_id:
            raise ValueError(
                f"Could not find calendar appointment for booking {booking_id}"
            )
        
        # Update via calendar API
        update_data = {
            "appointment_date": new_start_dt.date().isoformat(),
            "start_time": new_start_dt.time().strftime('%H:%M'),
            "end_time": new_end_dt.time().strftime('%H:%M'),
            "observations": f"Remarcado. Original: {appointment.start_ts.isoformat()}"
        }
        
        await calendar_client.update_appointment(
            calendar_appointment_id,
            update_data
        )
        
        logger.info(
            f"Updated calendar appointment: {calendar_appointment_id} "
            f"to {new_start_datetime}"
        )
        
        # Update our database
        await repo_reschedule_appointment(
            appointment.id,
            new_start_dt,
            new_end_dt
        )
        
        new_reschedule_count = appointment.reschedule_count + 1
        remaining = settings.max_reschedule_count - new_reschedule_count
        
        logger.info(
            f"Successfully rescheduled booking: {booking_id}, "
            f"count={new_reschedule_count}"
        )
        
        return {
            "success": True,
            "booking_id": booking_id,
            "calendar_appointment_id": calendar_appointment_id,
            "old_start_datetime": appointment.start_ts.isoformat(),
            "new_start_datetime": new_start_dt.isoformat(),
            "new_end_datetime": new_end_dt.isoformat(),
            "reschedule_count": new_reschedule_count,
            "remaining_reschedules": remaining,
            "message": (
                f"Agendamento remarcado com sucesso. "
                f"Você ainda pode remarcar {remaining} vez(es)."
            ),
            "service_name": service.name
        }
        
    except ValueError as e:
        logger.error(f"Validation error in reschedule_booking: {e}")
        raise
    except CalendarAPIError as e:
        logger.error(f"Calendar API error in reschedule_booking: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in reschedule_booking: {e}")
        raise


async def check_cancellation_policy(
    booking_id: str
) -> Dict[str, Any]:
    """
    Check if a booking can be cancelled according to policy.
    
    This is a helper function for agents to check policy before
    attempting cancellation. Also includes patient's no-show history.
    
    Requirements: 18.3, 18.4
    
    Args:
        booking_id: Appointment UUID
        
    Returns:
        Dictionary with policy information:
        {
            "can_cancel": true,
            "hours_before": 48,
            "required_hours": 24,
            "service_name": "Depilação a Laser",
            "appointment_datetime": "2025-10-17T14:00:00",
            "no_show_count": 0,
            "message": "Cancellation allowed"
        }
    """
    try:
        # Get appointment
        appointment = await get_appointment_by_id(UUID(booking_id))
        if not appointment:
            raise ValueError(f"Booking {booking_id} not found")
        
        # Get service
        service = await get_service_by_id(appointment.service_id)
        if not service:
            raise ValueError(f"Service {appointment.service_id} not found")
        
        # Get contact to check no-show history
        contact = await get_contact_by_id(appointment.contact_id)
        no_show_count = contact.no_show_count if contact else 0
        
        # Get policy hours
        required_hours = await get_cancellation_policy_hours(appointment.service_id)
        
        # Calculate hours before (match tz awareness)
        now = _now_matching(appointment.start_ts)
        hours_before = (appointment.start_ts - now).total_seconds() / 3600
        
        can_cancel = hours_before >= float(required_hours)
        
        # Build message with no-show warning if applicable
        message = "Cancelamento permitido" if can_cancel else \
                  f"Cancelamento fora do prazo. Necessário {required_hours}h de antecedência."
        
        if no_show_count > 0:
            message += f" (Histórico: {no_show_count} no-show(s) anterior(es))"
        
        result = {
            "can_cancel": can_cancel,
            "hours_before": round(hours_before, 1),
            "required_hours": required_hours,
            "service_name": service.name,
            "appointment_datetime": appointment.start_ts.isoformat(),
            "no_show_count": no_show_count,
            "message": message
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking cancellation policy: {e}")
        raise


# Tool metadata for AutoGen registration
RESCHEDULE_TOOLS = {
    "cancel_booking": {
        "function": cancel_booking,
        "description": (
            "Cancel an appointment booking. "
            "Validates cancellation policy (4h for harmonization, 24h for laser). "
            "If policy is violated, the session will be counted as done. "
            "Use check_cancellation_policy first to inform the patient."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Appointment UUID from our database"
                },
                "reason": {
                    "type": "string",
                    "description": "Cancellation reason (optional)"
                }
            },
            "required": ["booking_id"]
        }
    },
    "reschedule_booking": {
        "function": reschedule_booking,
        "description": (
            "Reschedule an appointment to a new time. "
            "Checks reschedule limit (maximum 2 reschedules). "
            "Validates cancellation policy and new time constraints. "
            "Always confirm new time with patient before calling."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Appointment UUID from our database"
                },
                "new_start_datetime": {
                    "type": "string",
                    "description": "New start datetime (ISO format: YYYY-MM-DDTHH:MM:SS)"
                }
            },
            "required": ["booking_id", "new_start_datetime"]
        }
    },
    "check_cancellation_policy": {
        "function": check_cancellation_policy,
        "description": (
            "Check if a booking can be cancelled according to policy. "
            "Use this before attempting cancellation to inform the patient "
            "about policy compliance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Appointment UUID from our database"
                }
            },
            "required": ["booking_id"]
        }
    }
}
