"""
Reminder job for sending appointment reminders.
Runs every 30 minutes to send D-1 and H-2 reminders.
Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from services.container import get_supabase_client
from config.settings import settings
from models.database import Appointment
from models.repository import mark_reminder_sent, get_service_by_id, get_contact_by_id
from agents.followup import create_followup_agent

logger = logging.getLogger(__name__)


async def send_d1_reminders() -> Dict[str, Any]:
    """
    Send D-1 reminders for appointments 18-26 hours in the future.
    
    Requirements: 7.2, 7.3, 7.4, 7.8
    
    Returns:
        Dictionary with job results:
        {
            "reminders_sent": 5,
            "reminders_failed": 0,
            "appointments_checked": 10
        }
    """
    try:
        logger.info("Starting D-1 reminder job")
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        now = datetime.utcnow()
        
        # Calculate time window: 18-26 hours from now
        start_window = now + timedelta(hours=18)
        end_window = now + timedelta(hours=26)
        
        # Query appointments in the time window that haven't received D-1 reminder
        response = supabase.table('appointments').select('*').gte(
            'start_ts', start_window.isoformat()
        ).lte(
            'start_ts', end_window.isoformat()
        ).eq('status', 'confirmed').eq('reminder_d1_sent', False).execute()
        
        appointments = [Appointment(**apt) for apt in response.data]
        
        logger.info(
            f"Found {len(appointments)} appointments eligible for D-1 reminder"
        )
        
        if not appointments:
            return {
                "reminders_sent": 0,
                "reminders_failed": 0,
                "appointments_checked": 0
            }
        
        # Initialize followup agent
        llm_config = {
            "provider": settings.MODEL_PROVIDER,
            "model": settings.GEMINI_MODEL if settings.MODEL_PROVIDER == "gemini" else settings.XAI_MODEL,
            "api_key": settings.GEMINI_API_KEY if settings.MODEL_PROVIDER == "gemini" else settings.XAI_API_KEY,
        }
        followup_agent = create_followup_agent(llm_config)
        
        reminders_sent = 0
        reminders_failed = 0
        
        for appointment in appointments:
            try:
                # Get contact and service details
                contact = await get_contact_by_id(appointment.contact_id)
                service = await get_service_by_id(appointment.service_id)
                
                if not contact or not service:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"contact or service not found"
                    )
                    reminders_failed += 1
                    continue
                
                # Check if we have conversation_id
                if not appointment.conversation_id:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"no conversation_id"
                    )
                    reminders_failed += 1
                    continue
                
                # Format appointment details
                appointment_date = appointment.start_ts.strftime("%d/%m/%Y")
                appointment_time = appointment.start_ts.strftime("%H:%M")
                
                # Get room name if available
                room_name = "A definir"
                if appointment.room_id:
                    room_response = supabase.table('rooms').select('name').eq(
                        'id', str(appointment.room_id)
                    ).execute()
                    if room_response.data:
                        room_name = room_response.data[0]['name']
                
                # Send reminder
                result = await followup_agent.send_reminder_d1(
                    conversation_id=int(appointment.conversation_id),
                    contact_name=contact.name or "Paciente",
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    procedure=service.name,
                    room=room_name
                )
                
                if result['success']:
                    # Mark reminder as sent
                    await mark_reminder_sent(appointment.id, 'd1')
                    reminders_sent += 1
                    
                    logger.info(
                        f"D-1 reminder sent successfully: "
                        f"appointment_id={appointment.id}, "
                        f"contact={contact.name}"
                    )
                else:
                    reminders_failed += 1
                    logger.error(
                        f"Failed to send D-1 reminder: "
                        f"appointment_id={appointment.id}, "
                        f"error={result.get('error')}"
                    )
            
            except Exception as e:
                reminders_failed += 1
                logger.error(
                    f"Error sending D-1 reminder for appointment {appointment.id}: {e}",
                    exc_info=True
                )
        
        result = {
            "reminders_sent": reminders_sent,
            "reminders_failed": reminders_failed,
            "appointments_checked": len(appointments)
        }
        
        logger.info(
            f"D-1 reminder job completed: {result}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in D-1 reminder job: {e}", exc_info=True)
        return {
            "reminders_sent": 0,
            "reminders_failed": 0,
            "appointments_checked": 0,
            "error": str(e)
        }


async def send_h2_reminders() -> Dict[str, Any]:
    """
    Send H-2 reminders for appointments 1.5-2.5 hours in the future.
    
    Requirements: 7.5, 7.6, 7.7, 7.8
    
    Returns:
        Dictionary with job results:
        {
            "reminders_sent": 3,
            "reminders_failed": 0,
            "appointments_checked": 5
        }
    """
    try:
        logger.info("Starting H-2 reminder job")
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        # Calculate time window: 1.5-2.5 hours from now
        start_window = now + timedelta(hours=1.5)
        end_window = now + timedelta(hours=2.5)
        
        # Query appointments in the time window that haven't received H-2 reminder
        response = supabase.table('appointments').select('*').gte(
            'start_ts', start_window.isoformat()
        ).lte(
            'start_ts', end_window.isoformat()
        ).eq('status', 'confirmed').eq('reminder_h2_sent', False).execute()
        
        appointments = [Appointment(**apt) for apt in response.data]
        
        logger.info(
            f"Found {len(appointments)} appointments eligible for H-2 reminder"
        )
        
        if not appointments:
            return {
                "reminders_sent": 0,
                "reminders_failed": 0,
                "appointments_checked": 0
            }
        
        # Initialize followup agent
        llm_config = {
            "provider": settings.MODEL_PROVIDER,
            "model": settings.GEMINI_MODEL if settings.MODEL_PROVIDER == "gemini" else settings.XAI_MODEL,
            "api_key": settings.GEMINI_API_KEY if settings.MODEL_PROVIDER == "gemini" else settings.XAI_API_KEY,
        }
        followup_agent = create_followup_agent(llm_config)
        
        reminders_sent = 0
        reminders_failed = 0
        
        for appointment in appointments:
            try:
                # Get contact and service details
                contact = await get_contact_by_id(appointment.contact_id)
                service = await get_service_by_id(appointment.service_id)
                
                if not contact or not service:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"contact or service not found"
                    )
                    reminders_failed += 1
                    continue
                
                # Check if we have conversation_id
                if not appointment.conversation_id:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"no conversation_id"
                    )
                    reminders_failed += 1
                    continue
                
                # Format appointment time
                appointment_time = appointment.start_ts.strftime("%H:%M")
                
                # Send reminder
                result = await followup_agent.send_reminder_h2(
                    conversation_id=int(appointment.conversation_id),
                    contact_name=contact.name or "Paciente",
                    appointment_time=appointment_time,
                    procedure=service.name
                )
                
                if result['success']:
                    # Mark reminder as sent
                    await mark_reminder_sent(appointment.id, 'h2')
                    reminders_sent += 1
                    
                    logger.info(
                        f"H-2 reminder sent successfully: "
                        f"appointment_id={appointment.id}, "
                        f"contact={contact.name}"
                    )
                else:
                    reminders_failed += 1
                    logger.error(
                        f"Failed to send H-2 reminder: "
                        f"appointment_id={appointment.id}, "
                        f"error={result.get('error')}"
                    )
            
            except Exception as e:
                reminders_failed += 1
                logger.error(
                    f"Error sending H-2 reminder for appointment {appointment.id}: {e}",
                    exc_info=True
                )
        
        result = {
            "reminders_sent": reminders_sent,
            "reminders_failed": reminders_failed,
            "appointments_checked": len(appointments)
        }
        
        logger.info(
            f"H-2 reminder job completed: {result}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in H-2 reminder job: {e}", exc_info=True)
        return {
            "reminders_sent": 0,
            "reminders_failed": 0,
            "appointments_checked": 0,
            "error": str(e)
        }


async def run_reminder_job() -> Dict[str, Any]:
    """
    Run both D-1 and H-2 reminder jobs.
    
    This function is called by the scheduler every 30 minutes.
    
    Returns:
        Dictionary with combined results from both jobs
    """
    logger.info("Starting reminder job (D-1 and H-2)")
    
    try:
        # Run D-1 reminders
        d1_results = await send_d1_reminders()
        
        # Run H-2 reminders
        h2_results = await send_h2_reminders()
        
        combined_results = {
            "d1_reminders": d1_results,
            "h2_reminders": h2_results,
            "total_sent": d1_results.get("reminders_sent", 0) + h2_results.get("reminders_sent", 0),
            "total_failed": d1_results.get("reminders_failed", 0) + h2_results.get("reminders_failed", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Reminder job completed: "
            f"total_sent={combined_results['total_sent']}, "
            f"total_failed={combined_results['total_failed']}"
        )
        
        return combined_results
    
    except Exception as e:
        logger.error(f"Error in reminder job: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }