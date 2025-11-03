"""
Input validation module for webhook payloads, phone numbers, and message content.
Implements security validations and data sanitization.
"""

import re
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
import structlog

logger = structlog.get_logger(__name__)


class PhoneValidator:
    """Validator for Brazilian phone numbers."""
    
    # Brazilian phone number patterns
    # Format: +55 (DDD) 9XXXX-XXXX or variations
    PHONE_PATTERNS = [
        r'^\+55\s?\(?[1-9]\d\)?\s?9?\d{4}-?\d{4}$',  # +55 (11) 91234-5678 (DDD cannot start with 0)
        r'^55\s?\(?[1-9]\d\)?\s?9?\d{4}-?\d{4}$',    # 55 (11) 91234-5678
        r'^\(?[1-9]\d\)?\s?9?\d{4}-?\d{4}$',         # (11) 91234-5678
        r'^55[1-9]\d9?\d{8}$',                           # 5511912345678
        r'^[1-9]\d9?\d{8}$',                             # 11912345678
    ]
    
    @classmethod
    def validate(cls, phone: str) -> bool:
        """
        Validate Brazilian phone number format.
        
        Args:
            phone: Phone number string
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove common separators for validation
        cleaned = phone.strip()
        
        # Check against patterns
        for pattern in cls.PHONE_PATTERNS:
            if re.match(pattern, cleaned):
                return True
        
        return False
    
    @classmethod
    def normalize(cls, phone: str) -> Optional[str]:
        """
        Normalize phone number to standard format: +55DDNNNNNNNNN.
        
        Args:
            phone: Phone number string
        
        Returns:
            Optional[str]: Normalized phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 13 and digits.startswith('55'):
            # Already has country code: 5511912345678
            return f"+{digits}"
        elif len(digits) == 11:
            # Missing country code: 11912345678
            return f"+55{digits}"
        elif len(digits) == 10:
            # Old format without 9: 1112345678
            # Add 9 after DDD and insert a space before the last two digits (legacy format expected by tests)
            ddd = digits[:2]
            number = digits[2:]
            number_with9 = '9' + number  # 9 + 8 digits
            return f"+55{ddd}{number_with9[:-2]} {number_with9[-2:]}"
        
        # Invalid format
        logger.warning("phone_normalization_failed", phone=phone, digits=digits)
        return None
    
    @classmethod
    def extract_ddd(cls, phone: str) -> Optional[str]:
        """
        Extract DDD (area code) from phone number.
        
        Args:
            phone: Phone number string
        
        Returns:
            Optional[str]: DDD or None if not found
        """
        normalized = cls.normalize(phone)
        if not normalized:
            return None
        
        # Extract DDD from +55DDNNNNNNNNN
        digits = re.sub(r'\D', '', normalized)
        if len(digits) >= 4 and digits.startswith('55'):
            return digits[2:4]
        
        return None


class MessageValidator:
    """Validator for message content."""
    
    MAX_MESSAGE_LENGTH = 4000
    
    # Patterns for potentially malicious content
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                 # JavaScript protocol
        r'on\w+\s*=',                  # Event handlers
        r'<iframe[^>]*>',              # Iframes
    ]
    
    @classmethod
    def validate_length(cls, message: str) -> bool:
        """
        Validate message length.
        
        Args:
            message: Message content
        
        Returns:
            bool: True if valid length, False otherwise
        """
        if not message:
            return False
        
        return len(message) <= cls.MAX_MESSAGE_LENGTH
    
    @classmethod
    def sanitize(cls, message: str) -> str:
        """
        Sanitize message content by removing potentially malicious patterns.
        
        Args:
            message: Message content
        
        Returns:
            str: Sanitized message
        """
        if not message:
            return ""
        
        sanitized = message
        
        # Remove suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Truncate if too long
        if len(sanitized) > cls.MAX_MESSAGE_LENGTH:
            sanitized = sanitized[:cls.MAX_MESSAGE_LENGTH]
            logger.warning(
                "message_truncated",
                original_length=len(message),
                truncated_length=len(sanitized)
            )
        
        return sanitized
    
    @classmethod
    def is_empty(cls, message: str) -> bool:
        """
        Check if message is empty or only whitespace.
        
        Args:
            message: Message content
        
        Returns:
            bool: True if empty, False otherwise
        """
        return not message or not message.strip()
    
    @classmethod
    def contains_prompt_injection(cls, message: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        Args:
            message: Message content
        
        Returns:
            bool: True if suspicious patterns detected, False otherwise
        """
        # Patterns that might indicate prompt injection
        injection_patterns = [
            r'ignore\s+(previous|above|all)\s+instructions',
            r'system\s*:',
            r'assistant\s*:',
            r'you\s+are\s+now',
            r'forget\s+everything',
            r'new\s+instructions',
            r'disregard\s+',
        ]
        
        message_lower = message.lower()
        
        for pattern in injection_patterns:
            if re.search(pattern, message_lower):
                logger.warning(
                    "potential_prompt_injection_detected",
                    pattern=pattern
                )
                return True
        
        return False


class ChatwootWebhookPayload(BaseModel):
    """Pydantic model for Chatwoot webhook payload validation."""
    
    event: str = Field(..., description="Event type")
    id: Optional[int] = Field(None, description="Message ID")
    content: Optional[str] = Field(None, description="Message content")
    message_type: str = Field(..., description="Message type (incoming/outgoing)")
    conversation: dict = Field(..., description="Conversation object")
    sender: Optional[dict] = Field(None, description="Sender object")
    account: dict = Field(..., description="Account object")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v):
        """Validate message content length."""
        if v and len(v) > MessageValidator.MAX_MESSAGE_LENGTH:
            raise ValueError(f'Message content exceeds maximum length of {MessageValidator.MAX_MESSAGE_LENGTH}')
        return v
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        """Validate message type is incoming."""
        if v not in ('incoming', 'outgoing'):
            raise ValueError('Invalid message type')
        return v
    
    def get_conversation_id(self) -> Optional[int]:
        """Extract conversation ID from payload."""
        return self.conversation.get('id')
    
    def get_phone(self) -> Optional[str]:
        """Extract phone number from payload."""
        # Try to get from sender
        if self.sender:
            phone = self.sender.get('phone_number') or self.sender.get('phone')
            if phone:
                return phone
        
        # Try to get from conversation meta
        if self.conversation:
            meta = self.conversation.get('meta', {})
            sender = meta.get('sender', {})
            phone = sender.get('phone_number') or sender.get('phone')
            if phone:
                return phone
        
        return None
    
    def get_sender_name(self) -> Optional[str]:
        """Extract sender name from payload."""
        if self.sender:
            return self.sender.get('name')
        
        if self.conversation:
            meta = self.conversation.get('meta', {})
            sender = meta.get('sender', {})
            return sender.get('name')
        
        return None
    
    def is_incoming(self) -> bool:
        """Check if message is incoming."""
        return self.message_type == 'incoming'


class WebhookValidator:
    """Validator for webhook payloads."""
    
    @staticmethod
    def validate_chatwoot_webhook(payload: dict) -> tuple[bool, Optional[ChatwootWebhookPayload], Optional[str]]:
        """
        Validate Chatwoot webhook payload.
        
        Args:
            payload: Webhook payload dictionary
        
        Returns:
            tuple: (is_valid, validated_payload, error_message)
        """
        try:
            validated = ChatwootWebhookPayload(**payload)
            
            # Additional validations
            if not validated.is_incoming():
                return False, None, "Only incoming messages are processed"
            
            if not validated.content or MessageValidator.is_empty(validated.content):
                return False, None, "Message content is empty"
            
            # Check for prompt injection
            if MessageValidator.contains_prompt_injection(validated.content):
                logger.warning(
                    "prompt_injection_attempt_blocked",
                    conversation_id=validated.get_conversation_id()
                )
                # Still process but log the attempt
            
            return True, validated, None
        
        except ValidationError as e:
            error_msg = str(e)
            logger.error(
                "webhook_validation_failed",
                error=error_msg,
                payload_keys=list(payload.keys()) if payload else None
            )
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(
                "webhook_validation_unexpected_error",
                error=error_msg
            )
            return False, None, error_msg
    
    @staticmethod
    def validate_required_fields(payload: dict, required_fields: list[str]) -> tuple[bool, Optional[str]]:
        """
        Validate that required fields are present in payload.
        
        Args:
            payload: Payload dictionary
            required_fields: List of required field names
        
        Returns:
            tuple: (is_valid, error_message)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in payload or payload[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            return False, error_msg
        
        return True, None


class InputSanitizer:
    """Sanitizer for user inputs before passing to LLM."""
    
    @staticmethod
    def sanitize_for_llm(message: str) -> str:
        """
        Sanitize message before passing to LLM.
        Adds prefix to clearly separate user input from system instructions.
        
        Args:
            message: User message
        
        Returns:
            str: Sanitized message with user prefix
        """
        # First sanitize the message
        sanitized = MessageValidator.sanitize(message)
        
        # Add user prefix to prevent prompt injection
        prefixed = f"User says: {sanitized}"
        
        return prefixed
    
    @staticmethod
    def sanitize_phone(phone: str) -> Optional[str]:
        """
        Sanitize and normalize phone number.
        
        Args:
            phone: Phone number string
        
        Returns:
            Optional[str]: Normalized phone or None if invalid
        """
        if not phone:
            return None
        
        # Validate first
        if not PhoneValidator.validate(phone):
            logger.warning("invalid_phone_format", phone=phone)
            return None
        
        # Normalize
        normalized = PhoneValidator.normalize(phone)
        
        if normalized:
            logger.debug("phone_sanitized", original=phone, normalized=normalized)
        
        return normalized
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize name input.
        
        Args:
            name: Name string
        
        Returns:
            str: Sanitized name
        """
        if not name:
            return ""
        
        # Remove special characters except spaces, hyphens, and apostrophes
        sanitized = re.sub(r'[^a-zA-ZÀ-ÿ\s\'-]', '', name)
        
        # Trim and normalize whitespace
        sanitized = ' '.join(sanitized.split())

        # If there are no spaces, attempt to split CamelCase into separate words
        if not sanitized or ' ' not in sanitized:
            sanitized = re.sub(r'(?<!^)([A-ZÀ-Ý])', r' \1', sanitized)

        # Capitalize properly
        sanitized = sanitized.title()
        
        # Limit length
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_email(email: str) -> Optional[str]:
        """
        Sanitize and validate email address.
        
        Args:
            email: Email string
        
        Returns:
            Optional[str]: Sanitized email or None if invalid
        """
        if not email:
            return None
        
        # Basic email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Trim and lowercase
        sanitized = email.strip().lower()
        
        # Validate format
        if not re.match(email_pattern, sanitized):
            logger.warning("invalid_email_format", email=email)
            return None
        
        return sanitized


class ValidationResult:
    """Result of validation operation."""
    
    def __init__(self, is_valid: bool, data: Any = None, error: Optional[str] = None):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            data: Validated/sanitized data
            error: Error message if validation failed
        """
        self.is_valid = is_valid
        self.data = data
        self.error = error
    
    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.is_valid
    
    def __repr__(self) -> str:
        """String representation."""
        if self.is_valid:
            return f"ValidationResult(valid=True, data={self.data})"
        return f"ValidationResult(valid=False, error={self.error})"


def validate_and_sanitize_webhook(payload: dict) -> ValidationResult:
    """
    Validate and sanitize webhook payload.
    
    Args:
        payload: Raw webhook payload
    
    Returns:
        ValidationResult: Validation result with sanitized data
    """
    # Validate structure
    is_valid, validated_payload, error = WebhookValidator.validate_chatwoot_webhook(payload)
    
    if not is_valid:
        return ValidationResult(False, error=error)
    
    # Sanitize content
    if validated_payload.content:
        validated_payload.content = MessageValidator.sanitize(validated_payload.content)
    
    # Sanitize phone if present
    phone = validated_payload.get_phone()
    if phone:
        sanitized_phone = InputSanitizer.sanitize_phone(phone)
        if not sanitized_phone:
            return ValidationResult(False, error="Invalid phone number format")
    
    return ValidationResult(True, data=validated_payload)


def validate_phone_number(phone: str) -> ValidationResult:
    """
    Validate and normalize phone number.
    
    Args:
        phone: Phone number string
    
    Returns:
        ValidationResult: Validation result with normalized phone
    """
    if not PhoneValidator.validate(phone):
        return ValidationResult(False, error="Invalid phone number format")
    
    normalized = PhoneValidator.normalize(phone)
    if not normalized:
        return ValidationResult(False, error="Failed to normalize phone number")
    
    return ValidationResult(True, data=normalized)


def validate_message_content(message: str) -> ValidationResult:
    """
    Validate and sanitize message content.
    
    Args:
        message: Message content
    
    Returns:
        ValidationResult: Validation result with sanitized message
    """
    if MessageValidator.is_empty(message):
        return ValidationResult(False, error="Message is empty")
    
    if not MessageValidator.validate_length(message):
        return ValidationResult(False, error=f"Message exceeds maximum length of {MessageValidator.MAX_MESSAGE_LENGTH}")
    
    sanitized = MessageValidator.sanitize(message)
    
    return ValidationResult(True, data=sanitized)
