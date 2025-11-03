"""
Feedback job for sending post-treatment feedback requests.
Runs daily at 10:00 to send feedback requests for completed appointments.
Requirements: 17.1, 17.2, 17.3, 17.5
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from services.container import get_supabase_client
from config.settings import settings
from models.database import Appointment
from models.repositories import get_contact_by_id, get_service_by_id
from models.repositories.logs import create_log_entry
from agents.followup import create_followup_agent

logger = logging.getLogger(__name__)


async def send_feedback_requests() -> Dict[str, Any]:
    """
    Send post-treatment feedback requests for appointments completed 24h ago.
    
    Requirements: 17.1, 17.2, 17.3, 17.5
    
    Returns:
        Dictionary with job results:
        {
            "feedback_sent": 3,
            "feedback_failed": 0,
            "appointments_checked": 5
        }
    """
    try:
        logger.info("Starting post-treatment feedback job")
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        now = datetime.utcnow()
        
        # Calculate time window: 23-25 hours ago (24h ± 1h)
        start_window = now - timedelta(hours=25)
        end_window = now - timedelta(hours=23)
        
        # Query completed appointments in the time window
        # We'll check for appointments that ended in this window
        response = supabase.table('appointments').select('*').gte(
            'end_ts', start_window.isoformat()
        ).lte(
            'end_ts', end_window.isoformat()
        ).eq('status', 'completed').execute()
        
        appointments = [Appointment(**apt) for apt in response.data]
        
        logger.info(
            f"Found {len(appointments)} completed appointments eligible for feedback"
        )
        
        if not appointments:
            return {
                "feedback_sent": 0,
                "feedback_failed": 0,
                "appointments_checked": 0
            }
        
        # Initialize followup agent
        llm_config = {
            "provider": settings.MODEL_PROVIDER,
            "model": settings.GEMINI_MODEL if settings.MODEL_PROVIDER == "gemini" else settings.XAI_MODEL,
            "api_key": settings.GEMINI_API_KEY if settings.MODEL_PROVIDER == "gemini" else settings.XAI_API_KEY,
        }
        followup_agent = create_followup_agent(llm_config)
        
        feedback_sent = 0
        feedback_failed = 0
        
        for appointment in appointments:
            try:
                # Check if feedback was already sent
                # We'll use a custom field or check logs to avoid duplicates
                # For now, we'll check if there's a log entry for this appointment
                log_check = supabase.table('logs').select('id').eq(
                    'conversation_id', appointment.conversation_id
                ).eq('intent', 'feedback').execute()
                
                if log_check.data and len(log_check.data) > 0:
                    logger.info(
                        f"Skipping appointment {appointment.id}: "
                        f"feedback already sent"
                    )
                    continue
                
                # Get contact and service details
                contact = await get_contact_by_id(appointment.contact_id)
                service = await get_service_by_id(appointment.service_id)
                
                if not contact or not service:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"contact or service not found"
                    )
                    feedback_failed += 1
                    continue
                
                # Check if we have conversation_id
                if not appointment.conversation_id:
                    logger.warning(
                        f"Skipping appointment {appointment.id}: "
                        f"no conversation_id"
                    )
                    feedback_failed += 1
                    continue
                
                # Send feedback request
                result = await followup_agent.send_post_treatment_feedback(
                    conversation_id=int(appointment.conversation_id),
                    contact_name=contact.name or "Paciente",
                    procedure=service.name
                )
                
                if result['success']:
                    # Log feedback sent to avoid duplicates
                    await create_log_entry(
                        conversation_id=appointment.conversation_id,
                        contact_id=appointment.contact_id,
                        intent='feedback',
                        provider=settings.MODEL_PROVIDER,
                        latency_ms=0,
                        tools_used=['send_post_treatment_feedback'],
                        cost_estimate=0.0
                    )
                    
                    feedback_sent += 1
                    
                    logger.info(
                        f"Feedback request sent successfully: "
                        f"appointment_id={appointment.id}, "
                        f"contact={contact.name}"
                    )
                else:
                    feedback_failed += 1
                    logger.error(
                        f"Failed to send feedback request: "
                        f"appointment_id={appointment.id}, "
                        f"error={result.get('error')}"
                    )
            
            except Exception as e:
                feedback_failed += 1
                logger.error(
                    f"Error sending feedback for appointment {appointment.id}: {e}",
                    exc_info=True
                )
        
        result = {
            "feedback_sent": feedback_sent,
            "feedback_failed": feedback_failed,
            "appointments_checked": len(appointments),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Post-treatment feedback job completed: {result}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in feedback job: {e}", exc_info=True)
        return {
            "feedback_sent": 0,
            "feedback_failed": 0,
            "appointments_checked": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def run_feedback_job() -> Dict[str, Any]:
    """
    Run the post-treatment feedback job.
    
    This function is called by the scheduler daily at 10:00.
    
    Returns:
        Dictionary with job results
    """
    logger.info("Starting daily feedback job")
    
    try:
        results = await send_feedback_requests()
        
        logger.info(
            f"Feedback job completed: "
            f"sent={results.get('feedback_sent', 0)}, "
            f"failed={results.get('feedback_failed', 0)}"
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Error in feedback job: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
