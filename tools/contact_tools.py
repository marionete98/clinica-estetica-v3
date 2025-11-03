"""
Contact management tools for AutoGen agents.
Provides functions for creating, updating, and retrieving contact information.
Requirements: 1.3, 10.1
"""

import re
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from models.repository import (
    create_or_update_contact as repo_create_or_update_contact,
    get_contact_by_phone as repo_get_contact_by_phone
)
from models.database import Contact

logger = logging.getLogger(__name__)


def validate_brazilian_phone(phone: str) -> bool:
    """
    Validate Brazilian phone number format according to Brazilian numbering plan.

    This function validates both mobile and landline numbers following
    the Brazilian numbering plan (Plano de Numeração Brasileiro).

    Accepted formats:
    - International: +55 11 99999-9999, +5511999999999
    - National: 11999999999, (11) 99999-9999, 11 99999-9999
    - With/without separators: spaces, hyphens, parentheses

    Validation rules:
    - Mobile numbers: 11 digits (DDD + 9 + 8 digits)
    - Landline numbers: 10 digits (DDD + 8 digits)
    - DDD (area code): 2 digits, both must be 1-9
    - Mobile: third digit must be 9

    Args:
        phone: Phone number string in any common Brazilian format

    Returns:
        bool: True if valid Brazilian phone number, False otherwise

    Example:
        >>> validate_brazilian_phone("+55 11 98765-4321")
        True
        >>> validate_brazilian_phone("11987654321")
        True
        >>> validate_brazilian_phone("1234567890")
        False

    Note:
        - Does not verify if the number actually exists
        - Only validates format according to Brazilian numbering rules
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it starts with +55 or just the number
    if cleaned.startswith('+55'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('55'):
        cleaned = cleaned[2:]
    
    # Brazilian mobile numbers: DDD (2 digits) + 9 + 8 digits = 11 digits
    # Brazilian landline: DDD (2 digits) + 8 digits = 10 digits
    if len(cleaned) == 11:
        # Mobile: starts with 9
        pattern = r'^[1-9][1-9]9\d{8}$'
    elif len(cleaned) == 10:
        # Landline
        pattern = r'^[1-9][1-9]\d{8}$'
    else:
        return False
    
    return bool(re.match(pattern, cleaned))


def normalize_brazilian_phone(phone: str) -> str:
    """
    Normalize Brazilian phone number to standard format: +5511999999999
    
    Args:
        phone: Phone number string
        
    Returns:
        Normalized phone number with +55 prefix
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not validate_brazilian_phone(phone):
        raise ValueError(f"Invalid Brazilian phone number: {phone}")
    
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Remove country code if present
    if cleaned.startswith('55'):
        cleaned = cleaned[2:]
    
    # Add country code
    normalized = f"+55{cleaned}"
    
    logger.debug(f"Normalized phone: {phone} -> {normalized}")
    
    return normalized


async def create_or_update_contact(
    phone: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    consent: bool = False
) -> Dict[str, Any]:
    """
    Create a new contact or update existing one by phone number.
    
    This function is designed to be called by AutoGen agents as a tool.
    It validates the phone number format, normalizes it, and stores/updates
    the contact in the Supabase database.
    
    Requirements: 1.3, 10.1
    
    Args:
        phone: Brazilian phone number (various formats accepted)
        name: Contact name (optional)
        email: Contact email (optional)
        consent: LGPD consent flag (default: False)
        
    Returns:
        Dictionary with contact information:
        {
            "id": "uuid",
            "phone": "+5511999999999",
            "name": "João Silva",
            "email": "joao@example.com",
            "consent": true,
            "no_show_count": 0,
            "created_at": "2025-10-16T10:00:00Z",
            "updated_at": "2025-10-16T10:00:00Z",
            "is_new": false
        }
        
    Raises:
        ValueError: If phone number is invalid
    """
    try:
        # Validate and normalize phone
        normalized_phone = normalize_brazilian_phone(phone)
        
        # Check if contact exists
        existing = await repo_get_contact_by_phone(normalized_phone)
        is_new = existing is None
        
        # Create or update contact
        contact = await repo_create_or_update_contact(
            phone=normalized_phone,
            name=name,
            email=email,
            consent=consent
        )
        
        logger.info(
            f"{'Created' if is_new else 'Updated'} contact: "
            f"phone={normalized_phone}, name={name}, email={email}"
        )
        
        # Convert to dictionary for agent consumption
        result = {
            "id": str(contact.id),
            "phone": contact.phone,
            "name": contact.name,
            "email": contact.email,
            "consent": contact.consent,
            "no_show_count": contact.no_show_count,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
            "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
            "is_new": is_new
        }
        
        return result
        
    except ValueError as e:
        logger.error(f"Invalid phone number: {phone} - {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating/updating contact: {e}")
        raise


async def get_contact_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve contact information by phone number.
    
    This function is designed to be called by AutoGen agents as a tool.
    It validates and normalizes the phone number before lookup.
    
    Requirements: 1.3
    
    Args:
        phone: Brazilian phone number (various formats accepted)
        
    Returns:
        Dictionary with contact information or None if not found:
        {
            "id": "uuid",
            "phone": "+5511999999999",
            "name": "João Silva",
            "email": "joao@example.com",
            "consent": true,
            "no_show_count": 0,
            "created_at": "2025-10-16T10:00:00Z",
            "updated_at": "2025-10-16T10:00:00Z"
        }
        
    Raises:
        ValueError: If phone number is invalid
    """
    try:
        # Validate and normalize phone
        normalized_phone = normalize_brazilian_phone(phone)
        
        # Retrieve contact
        contact = await repo_get_contact_by_phone(normalized_phone)
        
        if contact is None:
            logger.info(f"Contact not found: phone={normalized_phone}")
            return None
        
        logger.info(f"Retrieved contact: phone={normalized_phone}, name={contact.name}")
        
        # Convert to dictionary for agent consumption
        result = {
            "id": str(contact.id),
            "phone": contact.phone,
            "name": contact.name,
            "email": contact.email,
            "consent": contact.consent,
            "no_show_count": contact.no_show_count,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
            "updated_at": contact.updated_at.isoformat() if contact.updated_at else None
        }
        
        return result
        
    except ValueError as e:
        logger.error(f"Invalid phone number: {phone} - {e}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving contact: {e}")
        raise


# Tool metadata for AutoGen registration
CONTACT_TOOLS = {
    "create_or_update_contact": {
        "function": create_or_update_contact,
        "description": (
            "Create a new contact or update existing contact information. "
            "Use this when a patient provides their name, phone, or email. "
            "The phone number will be validated and normalized automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Brazilian phone number in any common format"
                },
                "name": {
                    "type": "string",
                    "description": "Contact's full name"
                },
                "email": {
                    "type": "string",
                    "description": "Contact's email address"
                },
                "consent": {
                    "type": "boolean",
                    "description": "LGPD consent flag (default: false)"
                }
            },
            "required": ["phone"]
        }
    },
    "get_contact_by_phone": {
        "function": get_contact_by_phone,
        "description": (
            "Retrieve contact information by phone number. "
            "Use this to check if a patient already exists in the system "
            "or to retrieve their information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Brazilian phone number in any common format"
                }
            },
            "required": ["phone"]
        }
    }
}
