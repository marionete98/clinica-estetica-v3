# Tools Module - Clínica Luana Multi-Agent System

This module provides all the tools (functions) that AutoGen agents can use to interact with external systems and perform business logic operations.

## Overview

The tools are organized into 5 main categories:

1. **Calendar API Client** - HTTP client for the external calendar system
2. **Contact Tools** - Patient contact management
3. **Knowledge Base Tools** - Clinic information and message templates
4. **Scheduler Tools** - Appointment booking and availability
5. **Reschedule Tools** - Appointment cancellation and rescheduling

## Files

### `calendar_api_client.py`

HTTP client for interacting with the external calendar API at:
`https://clinica-luana-calendar-production.up.railway.app/api`

**Key Features:**
- Async HTTP client with retry logic (3 attempts with exponential backoff)
- Comprehensive error handling and logging
- Methods for CRUD operations on appointments
- WhatsApp notification sending
- Health check endpoint

**Main Methods:**
- `get_appointments(date, start_date, end_date, bypass_cache)` - List appointments
- `get_appointment_by_id(appointment_id, bypass_cache)` - Get single appointment
- `create_appointment(appointment_data)` - Create new appointment
- `update_appointment(appointment_id, updates)` - Update appointment
- `delete_appointment(appointment_id)` - Soft delete (mark as cancelled)
- `send_whatsapp_notification(appointment_id, notification_type, phone_override)` - Send WhatsApp
- `check_health()` - Health check

**Requirements Covered:** 2.1, 2.2, 3.1, 3.2, 7.1, 7.8

---

### `contact_tools.py`

Tools for managing patient contact information.

**Key Features:**
- Brazilian phone number validation and normalization
- Create or update contact records
- Retrieve contact by phone number
- LGPD consent tracking

**Main Functions:**
- `validate_brazilian_phone(phone)` - Validate phone format
- `normalize_brazilian_phone(phone)` - Normalize to +5511999999999 format
- `create_or_update_contact(phone, name, email, consent)` - Create/update contact
- `get_contact_by_phone(phone)` - Retrieve contact

**Phone Format Support:**
- `+5511999999999`
- `5511999999999`
- `11999999999`
- `(11) 99999-9999`
- `11 99999-9999`
- `+55 11 99999-9999`

**Requirements Covered:** 1.3, 10.1

---

### `kb_tools.py` & `kb_tools_cached.py`

Tools for searching the clinic's knowledge base and retrieving message templates.

**Key Features:**
- Keyword-based search in knowledge base
- Message template retrieval
- Template formatting with variables
- Category filtering
- Redis caching for improved performance (cached version)

**Main Functions:**
- `search_knowledge_base(query, top_k, category)` - Search KB articles
- `get_message_template(template_name)` - Get template by name
- `list_available_templates(category)` - List all template names
- `format_template(template_name, variables)` - Format template with values
- `get_cache_statistics()` - Get Redis cache statistics (cached version only)

**Cache Statistics (kb_tools_cached.py):**
The `get_cache_statistics()` function returns:
- `kb_entries` - Number of knowledge base entries cached
- `templates` - Number of templates cached
- `total_keys` - Total number of keys in Redis cache
- `status` - Cache health status ("healthy" or "error")

**Use Cases:**
- Treatment information queries
- Pricing questions
- Policy explanations
- Contraindications and post-care
- Standardized messages
- Cache monitoring and diagnostics

**Requirements Covered:** 5.1, 5.2, 5.4

---

### `scheduler_tools.py`

Tools for appointment scheduling and availability checking.

**Key Features:**
- Business hours validation (Mon-Fri 08:30-19:00, Sat 08:30-12:00)
- Minimum advance time validation (1 hour)
- Conflict detection with existing appointments
- 10-minute interval between procedures
- Room and equipment allocation

**Main Functions:**
- `list_available_slots(service_id, date_range, start_date)` - Find available times
- `create_booking(contact_id, service_id, start_datetime, conversation_id)` - Create appointment
- `get_patient_bookings(phone)` - Get patient's appointments

**Business Rules:**
- Minimum 1 hour advance booking
- Business hours: Mon-Fri 08:30-19:00, Sat 08:30-12:00, Sun closed
- 10-minute interval between procedures
- Validates room and equipment availability

**Requirements Covered:** 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 16.2, 16.3

---

### `reschedule_tools.py`

Tools for canceling and rescheduling appointments with policy validation.

**Key Features:**
- Cancellation policy validation (4h harmonization, 24h laser)
- Reschedule limit enforcement (maximum 2 reschedules)
- No-show tracking for policy violations
- Policy compliance checking

**Main Functions:**
- `cancel_booking(booking_id, reason)` - Cancel appointment
- `reschedule_booking(booking_id, new_start_datetime)` - Reschedule appointment
- `check_cancellation_policy(booking_id)` - Check if cancellation allowed

**Cancellation Policies:**
- **Harmonization (facial/corporal):** 4 hours advance
- **Laser hair removal:** 24 hours advance
- **Policy violation:** Session counted as done (no-show)

**Reschedule Rules:**
- Maximum 2 reschedules per appointment
- Must comply with cancellation policy for current time
- New time must meet minimum advance requirement

**Requirements Covered:** 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8

---

## Tool Registry

All tools are registered in the `ALL_TOOLS` dictionary in `__init__.py`, which provides:

- Function reference
- Description for LLM understanding
- Parameter schema (JSON Schema format)
- Required vs optional parameters

This registry is used by AutoGen agents to discover and call tools.

## Usage Example

```python
from tools import (
    create_or_update_contact,
    list_available_slots,
    create_booking
)

# Create contact
contact = await create_or_update_contact(
    phone="11999999999",
    name="João Silva",
    email="joao@example.com",
    consent=True
)

# Find available slots
slots = await list_available_slots(
    service_id="uuid-here",
    date_range=7
)

# Create booking
booking = await create_booking(
    contact_id=contact["id"],
    service_id="uuid-here",
    start_datetime="2025-10-17T14:00:00",
    conversation_id="chatwoot-conv-123"
)
```

## Integration with Calendar API

The tools integrate with the external calendar system via REST API:

**Data Flow:**
1. Our tools query/update via `CalendarAPIClient`
2. Calendar API manages the `appointments` table in its Supabase instance
3. We maintain our own tracking tables for:
   - Contacts (with consent and no-show count)
   - Services (with policies and pricing)
   - Appointments (for reschedule count tracking)
   - Sessions, logs (for observability)

**Field Mapping:**
- Our `services.name` → Calendar `procedure`
- Our `services.category` → Calendar `treatment`
- Our `contacts.name` → Calendar `client_name`
- Our `contacts.phone` → Calendar `client_phone`
- Our `rooms.name` → Calendar `room`

## Error Handling

All tools implement comprehensive error handling:

- **Validation errors:** Raised as `ValueError` with descriptive messages
- **API errors:** Raised as `CalendarAPIError` with status codes
- **Network errors:** Automatic retry with exponential backoff (3 attempts)
- **Logging:** Structured logging at INFO, WARNING, and ERROR levels

## Testing

Basic tests are provided in `tests/test_tools.py`:

- Phone validation and normalization
- File structure verification
- Module import checks

Run tests with:
```bash
pytest tests/test_tools.py -v
```

## Configuration

Tools use settings from `config/settings.py`:

- `CALENDAR_API_URL` - Calendar API base URL
- `CALENDAR_API_TIMEOUT` - Request timeout (default: 10s)
- `MIN_BOOKING_ADVANCE_HOURS` - Minimum advance time (default: 1h)
- `HARMONIZATION_CANCEL_HOURS` - Harmonization cancellation policy (default: 4h)
- `LASER_CANCEL_HOURS` - Laser cancellation policy (default: 24h)
- `MAX_RESCHEDULE_COUNT` - Maximum reschedules (default: 2)

## Dependencies

- `httpx` - Async HTTP client
- `tenacity` - Retry logic with exponential backoff
- `pydantic` - Data validation
- `supabase` - Database client
- Standard library: `logging`, `datetime`, `typing`, `uuid`, `re`

## Next Steps

After implementing these tools, the next phase is:

**Task 5: Implement AutoGen Agents**
- Supervisor Agent (intent routing)
- Intake Agent (contact collection)
- FAQ Agent (knowledge base queries)
- Scheduler Agent (booking management)
- Escalation Agent (human handoff)

The agents will use these tools to perform their specialized functions.
