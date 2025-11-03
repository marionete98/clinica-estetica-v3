"""
Database models using Pydantic for validation and serialization.
Requirements: 3.1, 3.2, 3.3
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator, EmailStr
import re


# ============================================================================
# CONTACT MODEL
# ============================================================================
class Contact(BaseModel):
    """Patient contact information model."""
    
    id: Optional[UUID] = None
    phone: str = Field(..., min_length=10, max_length=20)
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    consent: bool = False
    no_show_count: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('phone')
    def validate_brazilian_phone(cls, v):
        """Validate Brazilian phone number format."""
        # Remove non-numeric characters
        phone_digits = re.sub(r'\D', '', v)
        
        # Brazilian phone should have 10-11 digits (with area code)
        if len(phone_digits) < 10 or len(phone_digits) > 11:
            raise ValueError('Phone must have 10-11 digits including area code')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "(94) 99139-8585",
                "name": "Maria Silva",
                "email": "maria@example.com",
                "consent": True
            }
        }


# ============================================================================
# ROOM MODEL
# ============================================================================
class Room(BaseModel):
    """Treatment room model."""
    
    id: Optional[UUID] = None
    name: str = Field(..., max_length=100)
    room_type: Optional[str] = Field(None, max_length=50)
    active: bool = True
    created_at: Optional[datetime] = None
    
    @validator('room_type')
    def validate_room_type(cls, v):
        """Validate room type."""
        if v is not None:
            valid_types = ['treatment', 'consultation', 'laser', 'cryo', 'apartment']
            if v not in valid_types:
                raise ValueError(f'Room type must be one of: {", ".join(valid_types)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sala 02",
                "room_type": "laser",
                "active": True
            }
        }


# ============================================================================
# EQUIPMENT MODEL
# ============================================================================
class Equipment(BaseModel):
    """Medical equipment model."""
    
    id: Optional[UUID] = None
    name: str = Field(..., max_length=100)
    equipment_type: Optional[str] = Field(None, max_length=50)
    room_id: Optional[UUID] = None
    active: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Laser Galaxy Fiber",
                "equipment_type": "laser",
                "room_id": "123e4567-e89b-12d3-a456-426614174000",
                "active": True
            }
        }


# ============================================================================
# SERVICE MODEL
# ============================================================================
class Service(BaseModel):
    """Aesthetic procedure service model."""
    
    id: Optional[UUID] = None
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    duration_min: int = Field(..., gt=0, le=480)
    price_fixed: Optional[Decimal] = Field(None, ge=0)
    requires_consultation: bool = False
    consultation_price: Optional[Decimal] = Field(None, ge=0)
    cancellation_hours: int = Field(default=24, ge=0)
    room_id: Optional[UUID] = None
    equipment_id: Optional[UUID] = None
    active: bool = True
    description: Optional[str] = None
    contraindications: Optional[str] = None
    post_treatment_care: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('category')
    def validate_category(cls, v):
        """Validate service category."""
        if v is not None:
            valid_categories = ['Facial', 'Corporal', 'Pós-Operatório', 'Emagrecimento']
            if v not in valid_categories:
                raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v
    
    @validator('cancellation_hours')
    def validate_cancellation_hours(cls, v):
        """Validate cancellation hours (typically 4 or 24)."""
        if v not in [4, 24, 48]:
            raise ValueError('Cancellation hours should typically be 4, 24, or 48')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Depilação a Laser - Corpo Completo",
                "category": "Corporal",
                "duration_min": 90,
                "price_fixed": 350.00,
                "cancellation_hours": 24,
                "description": "Depilação a laser de corpo completo"
            }
        }


# ============================================================================
# APPOINTMENT MODEL
# ============================================================================
class Appointment(BaseModel):
    """Scheduled appointment model for internal tracking.
    
    Note: service_id is now optional since Calendar API is the source of truth.
    This model is used for internal tracking only.
    """
    
    id: Optional[UUID] = None
    contact_id: UUID
    service_id: Optional[UUID] = None  # Optional - not used with Calendar API
    room_id: Optional[UUID] = None
    equipment_id: Optional[UUID] = None
    conversation_id: Optional[str] = Field(None, max_length=255)
    start_ts: datetime
    end_ts: datetime
    status: str = Field(default='confirmed', max_length=20)
    reschedule_count: int = Field(default=0, ge=0, le=2)
    reminder_d1_sent: bool = False
    reminder_h2_sent: bool = False
    feedback_sent: bool = False
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        """Validate appointment status."""
        valid_statuses = ['confirmed', 'cancelled', 'no_show', 'completed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('end_ts')
    def validate_end_after_start(cls, v, values):
        """Validate that end time is after start time."""
        if 'start_ts' in values and v <= values['start_ts']:
            raise ValueError('end_ts must be after start_ts')
        return v
    
    @validator('reschedule_count')
    def validate_reschedule_limit(cls, v):
        """Validate reschedule count doesn't exceed limit of 2."""
        if v > 2:
            raise ValueError('Maximum 2 reschedules allowed')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "contact_id": "123e4567-e89b-12d3-a456-426614174000",
                "service_id": "123e4567-e89b-12d3-a456-426614174001",
                "start_ts": "2025-10-20T10:00:00Z",
                "end_ts": "2025-10-20T11:30:00Z",
                "status": "confirmed"
            }
        }


# ============================================================================
# SESSION MODEL
# ============================================================================
class Session(BaseModel):
    """Conversation session model for context management."""
    
    id: Optional[UUID] = None
    conversation_id: str = Field(..., max_length=255)
    contact_id: Optional[UUID] = None
    summary: Optional[str] = None
    last_intent: Optional[str] = Field(None, max_length=50)
    automation_paused: bool = False
    human_takeover_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('last_intent')
    def validate_intent(cls, v):
        """Validate intent type."""
        if v is not None:
            valid_intents = [
                'greeting', 'faq', 'schedule', 'reschedule', 
                'cancel', 'escalate', 'followup'
            ]
            if v not in valid_intents:
                raise ValueError(f'Intent must be one of: {", ".join(valid_intents)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "cw_conv_12345",
                "contact_id": "123e4567-e89b-12d3-a456-426614174000",
                "last_intent": "schedule",
                "automation_paused": False,
                "human_takeover_reason": None
            }
        }


# ============================================================================
# LOG MODEL
# ============================================================================
class Log(BaseModel):
    """Structured log entry for observability."""
    
    id: Optional[UUID] = None
    ts: Optional[datetime] = None
    conversation_id: Optional[str] = Field(None, max_length=255)
    contact_id: Optional[UUID] = None
    intent: Optional[str] = Field(None, max_length=50)
    provider: Optional[str] = Field(None, max_length=20)
    latency_ms: Optional[int] = Field(None, ge=0)
    tools_used: Optional[List[str]] = None
    cost_estimate: Optional[Decimal] = Field(None, ge=0)
    error_message: Optional[str] = None
    request_payload: Optional[dict] = None
    response_payload: Optional[dict] = None
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate LLM provider."""
        if v is not None and v not in ['xai', 'gemini']:
            raise ValueError('Provider must be either "xai" or "gemini"')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "cw_conv_12345",
                "intent": "schedule",
                "provider": "grok",
                "latency_ms": 3450,
                "tools_used": ["list_available_slots", "create_booking"],
                "cost_estimate": 0.0234
            }
        }


# ============================================================================
# MESSAGE TEMPLATE MODEL
# ============================================================================
class MessageTemplate(BaseModel):
    """Predefined message template model."""
    
    id: Optional[UUID] = None
    name: str = Field(..., max_length=100)
    content: str
    variables: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "D1_REMINDER",
                "content": "Olá {name}! Lembrete: você tem {service} agendado amanhã às {time} na {room}.",
                "variables": ["name", "service", "time", "room"],
                "category": "reminder"
            }
        }


# ============================================================================
# KNOWLEDGE BASE MODEL
# ============================================================================
class KnowledgeBase(BaseModel):
    """Knowledge base article model for FAQ."""
    
    id: Optional[UUID] = None
    title: str = Field(..., max_length=255)
    content: str
    category: Optional[str] = Field(None, max_length=50)
    version: Optional[str] = Field(None, max_length=20)
    keywords: Optional[List[str]] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Depilação a Laser - Informações Gerais",
                "content": "A depilação a laser é um procedimento...",
                "category": "treatments",
                "keywords": ["depilação", "laser", "pelos"],
                "active": True
            }
        }
