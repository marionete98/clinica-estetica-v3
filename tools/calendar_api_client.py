"""
Calendar API Client for Clínica Luana scheduling system.
Provides HTTP client for interacting with the external calendar API.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from config.settings import settings

logger = logging.getLogger(__name__)


class CalendarAPIError(Exception):
    """Base exception for Calendar API errors."""
    pass


class CalendarAPIClient:
    """
    HTTP client for the external calendar API.
    
    Provides methods to interact with appointments, including:
    - Listing appointments with filters
    - Creating new appointments
    - Updating existing appointments
    - Deleting (soft delete) appointments
    - Sending WhatsApp notifications
    - Health checks
    
    Implements retry logic with exponential backoff for resilience.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Calendar API client.
        
        Args:
            base_url: Base URL for the calendar API (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.calendar_api_url
        self.timeout = timeout or settings.calendar_api_timeout
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )
        
        logger.info(
            f"CalendarAPIClient initialized with base_url={self.base_url}, "
            f"timeout={self.timeout}s"
        )
    
    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def _log_request(self, method: str, url: str, **kwargs):
        """Log outgoing request."""
        logger.debug(f"Calendar API {method} {url}", extra=kwargs)
    
    def _log_response(self, response: httpx.Response):
        """Log API response."""
        logger.debug(
            f"Calendar API response: status={response.status_code}, "
            f"elapsed={response.elapsed.total_seconds():.3f}s"
        )
    
    def _handle_error(self, response: httpx.Response, context: str = ""):
        """
        Handle API error responses.
        
        Args:
            response: HTTP response object
            context: Additional context for error message
            
        Raises:
            CalendarAPIError: With detailed error information
        """
        try:
            error_data = response.json()
            error_msg = error_data.get("message", "Unknown error")
        except Exception:
            error_msg = response.text or "No error details"
        
        full_msg = f"Calendar API error {context}: {response.status_code} - {error_msg}"
        logger.error(full_msg)
        raise CalendarAPIError(full_msg)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def get_appointments(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        bypass_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get appointments with optional filters.
        
        Args:
            date: Specific date (YYYY-MM-DD format)
            start_date: Start date for range query (YYYY-MM-DD)
            end_date: End date for range query (YYYY-MM-DD)
            bypass_cache: If True, bypass API cache
            
        Returns:
            List of appointment dictionaries
            
        Raises:
            CalendarAPIError: If API request fails
        """
        url = self._build_url("/appointments")
        params = {}
        
        if date:
            params["date"] = date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if bypass_cache:
            params["bypass_cache"] = "true"
        
        self._log_request("GET", url, params=params)
        
        try:
            response = await self.client.get(url, params=params)
            self._log_response(response)
            
            if response.status_code != 200:
                self._handle_error(response, "getting appointments")
            
            data = response.json()
            appointments = data.get("data", [])
            
            logger.info(
                f"Retrieved {len(appointments)} appointments "
                f"(date={date}, start_date={start_date}, end_date={end_date})"
            )
            
            return appointments
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error getting appointments: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting appointments: {e}")
            raise CalendarAPIError(f"Failed to get appointments: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def get_appointment_by_id(
        self,
        appointment_id: str,
        bypass_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Get a specific appointment by ID.
        
        Args:
            appointment_id: Appointment UUID
            bypass_cache: If True, bypass API cache
            
        Returns:
            Appointment dictionary
            
        Raises:
            CalendarAPIError: If API request fails or appointment not found
        """
        url = self._build_url(f"/appointments/{appointment_id}")
        params = {}
        
        if bypass_cache:
            params["bypass_cache"] = "true"
        
        self._log_request("GET", url, params=params)
        
        try:
            response = await self.client.get(url, params=params)
            self._log_response(response)
            
            if response.status_code == 404:
                raise CalendarAPIError(f"Appointment {appointment_id} not found")
            
            if response.status_code != 200:
                self._handle_error(response, f"getting appointment {appointment_id}")
            
            data = response.json()
            appointment = data.get("data")
            
            logger.info(f"Retrieved appointment {appointment_id}")
            
            return appointment
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error getting appointment {appointment_id}: {e}")
            raise
        except CalendarAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting appointment {appointment_id}: {e}")
            raise CalendarAPIError(f"Failed to get appointment: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def create_appointment(
        self,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new appointment.
        
        Args:
            appointment_data: Appointment data dictionary with required fields:
                - client_name (required)
                - appointment_date (required, YYYY-MM-DD)
                - start_time (required, HH:MM)
                - end_time (required, HH:MM)
                - procedure (required)
                - treatment (required)
                Optional fields:
                - client_phone, client_email, duration, room, observations, status, color
                
        Returns:
            Created appointment dictionary with ID
            
        Raises:
            CalendarAPIError: If API request fails or validation fails
        """
        url = self._build_url("/appointments")
        
        # Validate required fields
        required_fields = [
            "client_name", "appointment_date", "start_time",
            "end_time", "procedure", "treatment"
        ]
        missing = [f for f in required_fields if f not in appointment_data]
        if missing:
            raise CalendarAPIError(
                f"Missing required fields for appointment creation: {missing}"
            )
        
        self._log_request("POST", url, json=appointment_data)
        
        try:
            response = await self.client.post(url, json=appointment_data)
            self._log_response(response)
            
            if response.status_code not in (200, 201):
                self._handle_error(response, "creating appointment")
            
            data = response.json()
            appointment = data.get("data")
            
            logger.info(
                f"Created appointment {appointment.get('id')} for "
                f"{appointment_data.get('client_name')} on "
                f"{appointment_data.get('appointment_date')} at "
                f"{appointment_data.get('start_time')}"
            )
            
            return appointment
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error creating appointment: {e}")
            raise
        except CalendarAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating appointment: {e}")
            raise CalendarAPIError(f"Failed to create appointment: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def update_appointment(
        self,
        appointment_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing appointment.
        
        Args:
            appointment_id: Appointment UUID
            updates: Dictionary with fields to update (partial update supported)
                
        Returns:
            Updated appointment dictionary
            
        Raises:
            CalendarAPIError: If API request fails or appointment not found
        """
        url = self._build_url(f"/appointments/{appointment_id}")
        
        self._log_request("PUT", url, json=updates)
        
        try:
            response = await self.client.put(url, json=updates)
            self._log_response(response)
            
            if response.status_code == 404:
                raise CalendarAPIError(f"Appointment {appointment_id} not found")
            
            if response.status_code != 200:
                self._handle_error(response, f"updating appointment {appointment_id}")
            
            data = response.json()
            appointment = data.get("data")
            
            logger.info(
                f"Updated appointment {appointment_id} with fields: "
                f"{list(updates.keys())}"
            )
            
            return appointment
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error updating appointment {appointment_id}: {e}")
            raise
        except CalendarAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating appointment {appointment_id}: {e}")
            raise CalendarAPIError(f"Failed to update appointment: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def delete_appointment(
        self,
        appointment_id: str
    ) -> Dict[str, Any]:
        """
        Delete an appointment (soft delete - marks as cancelled).
        
        Args:
            appointment_id: Appointment UUID
                
        Returns:
            Response dictionary with success message
            
        Raises:
            CalendarAPIError: If API request fails or appointment not found
        """
        url = self._build_url(f"/appointments/{appointment_id}")
        
        self._log_request("DELETE", url)
        
        try:
            response = await self.client.delete(url)
            self._log_response(response)
            
            if response.status_code == 404:
                raise CalendarAPIError(f"Appointment {appointment_id} not found")
            
            if response.status_code != 200:
                self._handle_error(response, f"deleting appointment {appointment_id}")
            
            data = response.json()
            
            logger.info(f"Deleted (soft) appointment {appointment_id}")
            
            return data
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error deleting appointment {appointment_id}: {e}")
            raise
        except CalendarAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting appointment {appointment_id}: {e}")
            raise CalendarAPIError(f"Failed to delete appointment: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def send_whatsapp_notification(
        self,
        appointment_id: str,
        notification_type: str,
        phone_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp notification for an appointment.
        
        Args:
            appointment_id: Appointment UUID
            notification_type: Type of notification:
                - 'confirmation': Booking confirmation
                - 'reminder': Reminder (24h before)
                - 'cancellation': Cancellation notice
                - 'rescheduled': Rescheduling notice
            phone_override: Optional phone number to override appointment's phone
                
        Returns:
            Response dictionary with notification details
            
        Raises:
            CalendarAPIError: If API request fails
        """
        url = self._build_url("/notifications/send-whatsapp")
        
        valid_types = ["confirmation", "reminder", "cancellation", "rescheduled"]
        if notification_type not in valid_types:
            raise CalendarAPIError(
                f"Invalid notification_type: {notification_type}. "
                f"Must be one of: {valid_types}"
            )
        
        payload = {
            "appointment_id": appointment_id,
            "notification_type": notification_type
        }
        
        if phone_override:
            payload["phone_override"] = phone_override
        
        self._log_request("POST", url, json=payload)
        
        try:
            response = await self.client.post(url, json=payload)
            self._log_response(response)
            
            if response.status_code != 200:
                self._handle_error(
                    response,
                    f"sending WhatsApp notification for appointment {appointment_id}"
                )
            
            data = response.json()
            
            logger.info(
                f"Sent WhatsApp {notification_type} notification for "
                f"appointment {appointment_id}"
            )
            
            return data
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(
                f"Network error sending WhatsApp notification for "
                f"appointment {appointment_id}: {e}"
            )
            raise
        except CalendarAPIError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error sending WhatsApp notification for "
                f"appointment {appointment_id}: {e}"
            )
            raise CalendarAPIError(f"Failed to send WhatsApp notification: {e}")
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health status of the calendar API.
        
        Returns:
            Health status dictionary
            
        Raises:
            CalendarAPIError: If API is unreachable or unhealthy
        """
        url = self._build_url("/health")
        
        self._log_request("GET", url)
        
        try:
            response = await self.client.get(url)
            self._log_response(response)
            
            if response.status_code != 200:
                self._handle_error(response, "checking health")
            
            data = response.json()
            
            status = data.get("status")
            if status != "healthy":
                logger.warning(f"Calendar API health check returned status: {status}")
            else:
                logger.info("Calendar API is healthy")
            
            return data
            
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(f"Calendar API is unreachable: {e}")
            raise CalendarAPIError(f"Calendar API unreachable: {e}")
        except Exception as e:
            logger.error(f"Unexpected error checking Calendar API health: {e}")
            raise CalendarAPIError(f"Failed to check health: {e}")


# Global client instance (to be initialized in app startup)
calendar_client: Optional[CalendarAPIClient] = None


async def get_calendar_client() -> CalendarAPIClient:
    """
    Get or create the global calendar client instance.
    
    Returns:
        CalendarAPIClient instance
    """
    global calendar_client
    
    if calendar_client is None:
        calendar_client = CalendarAPIClient()
    
    return calendar_client


async def close_calendar_client():
    """Close the global calendar client instance."""
    global calendar_client
    
    if calendar_client is not None:
        await calendar_client.close()
        calendar_client = None
