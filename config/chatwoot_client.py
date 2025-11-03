"""
Chatwoot client module for sending messages and managing conversations.
"""

import time
from typing import Any, Optional
from datetime import datetime, timedelta
import structlog
import httpx
from httpx import HTTPStatusError, RequestError

from config.settings import settings

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Simple rate limiter for API calls.
    """
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list[float] = []
    
    def is_allowed(self) -> bool:
        """
        Check if a request is allowed under rate limit.
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Remove requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """
        Get time to wait before next request is allowed.
        
        Returns:
            float: Seconds to wait
        """
        if not self.requests:
            return 0.0
        
        oldest_request = min(self.requests)
        time_passed = time.time() - oldest_request
        
        if time_passed >= self.time_window:
            return 0.0
        
        return self.time_window - time_passed


class ChatwootClient:
    """
    Chatwoot API client for message sending and conversation management.
    """
    
    def __init__(self):
        """Initialize Chatwoot client."""
        self.base_url = settings.chatwoot_api_url.rstrip("/")
        self.account_id = settings.chatwoot_account_id
        self.api_token = settings.chatwoot_api_token
        
        # Rate limiter: 100 requests per minute
        self.rate_limiter = RateLimiter(
            max_requests=settings.max_requests_per_minute,
            time_window=60
        )
        
        # HTTP client with timeout
        self.client = httpx.Client(
            timeout=10.0,
            headers={
                "api_access_token": self.api_token,
                "Content-Type": "application/json"
            }
        )
        
        logger.info(
            "chatwoot_client_initialized",
            base_url=self.base_url,
            account_id=self.account_id
        )
    
    def _get_api_url(self, endpoint: str) -> str:
        """
        Construct full API URL.
        
        Args:
            endpoint: API endpoint path
        
        Returns:
            str: Full API URL
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/api/v1/accounts/{self.account_id}/{endpoint}"
    
    def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit is exceeded."""
        if not self.rate_limiter.is_allowed():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(
                "chatwoot_rate_limit_exceeded",
                wait_time=wait_time
            )
            time.sleep(wait_time)
            # Try again after waiting
            self.rate_limiter.is_allowed()
    
    def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False
    ) -> Optional[dict[str, Any]]:
        """
        Send a message in a conversation with retry logic.
        
        Args:
            conversation_id: Chatwoot conversation ID
            content: Message content
            message_type: Message type ('outgoing' or 'incoming')
            private: If True, message is private (internal note)
        
        Returns:
            dict: Response data with message details or None on failure
        """
        max_retries = 3
        retry_delay = 1.0
        backoff = 2.0
        
        for attempt in range(max_retries):
            try:
                # Check rate limit
                self._wait_for_rate_limit()
                
                url = self._get_api_url(f"conversations/{conversation_id}/messages")
                
                payload = {
                    "content": content,
                    "message_type": message_type,
                    "private": private
                }
                
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(
                    "chatwoot_message_sent",
                    conversation_id=conversation_id,
                    message_id=data.get("id"),
                    attempt=attempt + 1
                )
                
                return data
            
            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit exceeded, wait longer
                    wait_time = retry_delay * (backoff ** attempt)
                    logger.warning(
                        "chatwoot_rate_limit_429",
                        conversation_id=conversation_id,
                        wait_time=wait_time
                    )
                    time.sleep(wait_time)
                    continue
                
                logger.error(
                    "chatwoot_message_send_http_error",
                    conversation_id=conversation_id,
                    status_code=e.response.status_code,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= backoff
                else:
                    return None
            
            except RequestError as e:
                logger.error(
                    "chatwoot_message_send_request_error",
                    conversation_id=conversation_id,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= backoff
                else:
                    return None
        
        return None
    
    def get_conversation(self, conversation_id: int) -> Optional[dict[str, Any]]:
        """
        Get conversation details.
        
        Args:
            conversation_id: Chatwoot conversation ID
        
        Returns:
            dict: Conversation data or None on failure
        """
        try:
            self._wait_for_rate_limit()
            
            url = self._get_api_url(f"conversations/{conversation_id}")
            response = self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            logger.debug(
                "chatwoot_conversation_retrieved",
                conversation_id=conversation_id
            )
            
            return data
        
        except (HTTPStatusError, RequestError) as e:
            logger.error(
                "chatwoot_get_conversation_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return None
    
    def assign_conversation(
        self,
        conversation_id: int,
        assignee_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> bool:
        """
        Assign conversation to a human agent or team.
        
        Args:
            conversation_id: Chatwoot conversation ID
            assignee_id: Agent ID to assign to (optional)
            team_id: Team ID to assign to (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._wait_for_rate_limit()
            
            url = self._get_api_url(f"conversations/{conversation_id}/assignments")
            
            payload = {}
            if assignee_id is not None:
                payload["assignee_id"] = assignee_id
            if team_id is not None:
                payload["team_id"] = team_id
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(
                "chatwoot_conversation_assigned",
                conversation_id=conversation_id,
                assignee_id=assignee_id,
                team_id=team_id
            )
            
            return True
        
        except (HTTPStatusError, RequestError) as e:
            logger.error(
                "chatwoot_assign_conversation_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    def toggle_status(
        self,
        conversation_id: int,
        status: str
    ) -> bool:
        """
        Toggle conversation status.
        
        Args:
            conversation_id: Chatwoot conversation ID
            status: Status to set ('open', 'resolved', 'pending')
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._wait_for_rate_limit()
            
            url = self._get_api_url(f"conversations/{conversation_id}/toggle_status")
            
            payload = {"status": status}
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(
                "chatwoot_conversation_status_changed",
                conversation_id=conversation_id,
                status=status
            )
            
            return True
        
        except (HTTPStatusError, RequestError) as e:
            logger.error(
                "chatwoot_toggle_status_failed",
                conversation_id=conversation_id,
                status=status,
                error=str(e)
            )
            return False
    
    def add_labels(
        self,
        conversation_id: int,
        labels: list[str]
    ) -> bool:
        """
        Add labels to a conversation.
        
        Args:
            conversation_id: Chatwoot conversation ID
            labels: List of label names to add
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._wait_for_rate_limit()
            
            url = self._get_api_url(f"conversations/{conversation_id}/labels")
            
            payload = {"labels": labels}
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(
                "chatwoot_labels_added",
                conversation_id=conversation_id,
                labels=labels
            )
            
            return True
        
        except (HTTPStatusError, RequestError) as e:
            logger.error(
                "chatwoot_add_labels_failed",
                conversation_id=conversation_id,
                labels=labels,
                error=str(e)
            )
            return False
    
    def create_conversation(
        self,
        inbox_id: int,
        contact_id: int,
        source_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Create a new conversation in a specific inbox.
        
        Args:
            inbox_id: Target inbox ID
            contact_id: Contact ID in Chatwoot
            source_id: Source identifier (e.g., phone number)
        
        Returns:
            dict: Conversation data or None on failure
        """
        try:
            self._wait_for_rate_limit()
            
            url = self._get_api_url("conversations")
            
            payload = {
                "inbox_id": inbox_id,
                "contact_id": contact_id,
                "source_id": source_id
            }
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(
                "chatwoot_conversation_created",
                conversation_id=data.get("id"),
                inbox_id=inbox_id,
                contact_id=contact_id
            )
            
            return data
        
        except (HTTPStatusError, RequestError) as e:
            logger.error(
                "chatwoot_create_conversation_failed",
                inbox_id=inbox_id,
                contact_id=contact_id,
                error=str(e)
            )
            return None
    
    def health_check(self) -> bool:
        """
        Check if Chatwoot API is accessible.
        
        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            # Try to get account details as health check
            url = f"{self.base_url}/api/v1/accounts/{self.account_id}"
            response = self.client.get(url)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error("chatwoot_health_check_failed", error=str(e))
            return False
    
    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()


# Global Chatwoot client instance
chatwoot_client = ChatwootClient()
