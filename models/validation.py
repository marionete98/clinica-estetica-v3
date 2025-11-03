"""
Input validation models using Pydantic.

This module provides comprehensive input validation for webhook payloads
and other user inputs using Pydantic models with custom validators.

Features:
- Phone number validation using phonenumbers library (Brazilian format)
- Message sanitization (control characters, length limits)
- Email validation using email-validator library
- Conversation ID validation
- Comprehensive error messages

Requirements: Phase 1, Task 1.4
"""

import re
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)


class ChatwootMessageInput(BaseModel):
    """
    Validation model for incoming Chatwoot webhook messages.
    
    This model validates and sanitizes all incoming webhook payloads
    to ensure data quality and security.
    
    Fields:
        conversation_id: Chatwoot conversation ID (1-50 chars)
        phone: Brazilian phone number (validated and normalized to E.164)
        message: Message content (sanitized, 1-4000 chars)
        timestamp: Unix timestamp (positive integer)
        sender: Sender information dictionary
    
    Example:
        ```python
        input_data = ChatwootMessageInput(
            conversation_id="12345",
            phone="+5511999999999",
            message="Olá, gostaria de agendar",
            timestamp=1697500000,
            sender={"id": 1, "name": "João"}
        )
        ```
    """
    
    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Chatwoot conversation ID"
    )
    
    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Brazilian phone number (will be normalized to E.164 format)"
    )
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message content (will be sanitized)"
    )
    
    timestamp: int = Field(
        ...,
        gt=0,
        description="Unix timestamp in seconds"
    )
    
    sender: Dict[str, Any] = Field(
        ...,
        description="Sender information dictionary"
    )
    
    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """
        Validate conversation ID format.
        
        Args:
            v: Conversation ID string
            
        Returns:
            str: Validated conversation ID
            
        Raises:
            ValueError: If conversation ID contains invalid characters
        """
        # Remove whitespace
        v = v.strip()
        
        # Check for empty after strip
        if not v:
            raise ValueError("Conversation ID cannot be empty or whitespace")
        
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "Conversation ID must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        """
        Validate and normalize Brazilian phone number to E.164 format.
        
        Uses the phonenumbers library for robust validation and formatting.
        Accepts various Brazilian phone formats and normalizes to +5511999999999.
        
        Args:
            v: Phone number string (various formats accepted)
            
        Returns:
            str: Normalized phone number in E.164 format (+5511999999999)
            
        Raises:
            ValueError: If phone number is invalid or not Brazilian
            
        Examples:
            - "+55 11 99999-9999" -> "+5511999999999"
            - "11999999999" -> "+5511999999999"
            - "(11) 99999-9999" -> "+5511999999999"
        """
        if not v:
            raise ValueError("Phone number cannot be empty")
        
        # Remove whitespace
        v = v.strip()
        
        try:
            # Parse phone number with Brazil as default region
            parsed = phonenumbers.parse(v, "BR")
            
            # Validate the parsed number
            if not phonenumbers.is_valid_number(parsed):
                digits = re.sub(r'\D+', '', v)
                digits_no_cc = digits[2:] if digits.startswith('55') else digits
                if digits_no_cc.startswith('0'):
                    digits_no_cc = digits_no_cc.lstrip('0')
                if len(digits_no_cc) == 10:
                    candidate = '+55' + digits_no_cc[:2] + '9' + digits_no_cc[2:]
                    try:
                        parsed_candidate = phonenumbers.parse(candidate, "BR")
                        if phonenumbers.is_valid_number(parsed_candidate) and parsed_candidate.country_code == 55:
                            normalized = phonenumbers.format_number(
                                parsed_candidate,
                                phonenumbers.PhoneNumberFormat.E164
                            )
                            logger.info(
                                "Phone auto-corrected by adding ninth digit",
                                extra={"original": v, "corrected": normalized}
                            )
                            return normalized
                    except Exception:
                        pass
                raise ValueError(
                    f"Invalid phone number: {v}. "
                    "Please provide a valid Brazilian phone number."
                )
            
            # Check if it's a Brazilian number
            if parsed.country_code != 55:
                raise ValueError(
                    f"Phone number must be Brazilian (country code +55), "
                    f"got country code +{parsed.country_code}"
                )
            
            # Format to E.164 (international format: +5511999999999)
            normalized = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            
            logger.debug(
                f"Phone normalized: {v} -> {normalized}",
                extra={"original": v, "normalized": normalized}
            )
            
            return normalized
            
        except NumberParseException as e:
            try:
                digits = re.sub(r'\D+', '', v)
                digits_no_cc = digits[2:] if digits.startswith('55') else digits
                if digits_no_cc.startswith('0'):
                    digits_no_cc = digits_no_cc.lstrip('0')
                if len(digits_no_cc) == 10:
                    candidate = '+55' + digits_no_cc[:2] + '9' + digits_no_cc[2:]
                    parsed_candidate = phonenumbers.parse(candidate, "BR")
                    if phonenumbers.is_valid_number(parsed_candidate) and parsed_candidate.country_code == 55:
                        normalized = phonenumbers.format_number(
                            parsed_candidate,
                            phonenumbers.PhoneNumberFormat.E164
                        )
                        logger.info(
                            "Phone auto-corrected by adding ninth digit",
                            extra={"original": v, "corrected": normalized}
                        )
                        return normalized
            except Exception:
                pass
            logger.warning(
                f"Phone parsing failed: {v} - {e}",
                extra={"phone": v, "error": str(e)}
            )
            raise ValueError(
                f"Invalid phone number format: {v}. "
                "Accepted formats: +5511999999999, 11999999999, (11) 99999-9999"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error validating phone: {v} - {e}",
                extra={"phone": v, "error": str(e)},
                exc_info=True
            )
            raise ValueError(f"Error validating phone number: {v}") from e
    
    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """
        Sanitize message content by removing control characters.
        
        Removes ASCII control characters (0x00-0x1F, 0x7F-0x9F) that could
        cause issues with storage, display, or processing. Preserves newlines
        and tabs for formatting.
        
        Args:
            v: Message content string
            
        Returns:
            str: Sanitized message content
            
        Raises:
            ValueError: If message is empty after sanitization
        """
        if not v:
            raise ValueError("Message cannot be empty")
        
        # Remove control characters except newline (\n), carriage return (\r), and tab (\t)
        # Control chars: 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F-0x9F
        sanitized = re.sub(
            r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]',
            '',
            v
        )
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        # Check if empty after sanitization
        if not sanitized:
            raise ValueError(
                "Message cannot be empty or contain only control characters"
            )
        
        # Log if sanitization changed the message
        if sanitized != v:
            logger.info(
                "Message sanitized (control characters removed)",
                extra={
                    "original_length": len(v),
                    "sanitized_length": len(sanitized),
                    "chars_removed": len(v) - len(sanitized)
                }
            )
        
        return sanitized
    
    @field_validator('sender')
    @classmethod
    def validate_sender(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sender information dictionary.
        
        Args:
            v: Sender information dictionary
            
        Returns:
            Dict[str, Any]: Validated sender dictionary
            
        Raises:
            ValueError: If sender is missing required fields
        """
        if not v:
            raise ValueError("Sender information cannot be empty")
        
        # Check for required fields
        if "id" not in v:
            raise ValueError("Sender must have 'id' field")
        
        return v
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "conversation_id": "12345",
                "phone": "+5511999999999",
                "message": "Olá, gostaria de agendar uma consulta",
                "timestamp": 1697500000,
                "sender": {
                    "id": 1,
                    "name": "João Silva",
                    "email": "joao@example.com"
                }
            }
        }
    )


class ContactInput(BaseModel):
    """
    Validation model for contact information.
    
    Used when creating or updating contact records.
    
    Fields:
        phone: Brazilian phone number (validated and normalized)
        name: Contact name (optional, 1-255 chars)
        email: Email address (optional, validated)
        consent: LGPD consent flag (default: False)
    """
    
    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Brazilian phone number"
    )
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Contact name"
    )
    
    email: Optional[EmailStr] = Field(
        None,
        description="Email address (validated)"
    )
    
    consent: bool = Field(
        default=False,
        description="LGPD consent flag"
    )
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number (same as ChatwootMessageInput)."""
        if not v:
            raise ValueError("Phone number cannot be empty")
        
        v = v.strip()
        
        try:
            parsed = phonenumbers.parse(v, "BR")
            
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Invalid phone number: {v}")
            
            if parsed.country_code != 55:
                raise ValueError(f"Phone must be Brazilian (country code +55)")
            
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            
        except NumberParseException as e:
            raise ValueError(f"Invalid phone format: {v}") from e
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize name by removing control characters."""
        if v is None:
            return None
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', v)
        sanitized = sanitized.strip()
        
        # Return None if empty after sanitization
        if not sanitized:
            return None
        
        return sanitized
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "+5511999999999",
                "name": "Maria Silva",
                "email": "maria@example.com",
                "consent": True
            }
        }
    )

