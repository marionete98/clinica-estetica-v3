# AutoGen Agents - Clínica Luana

This directory contains all AutoGen agents for the multi-agent scheduling system.

## Architecture

The system uses a **Supervisor-Worker** pattern where:
- **Supervisor Agent** classifies intent and routes to specialized agents
- **Worker Agents** handle specific tasks (intake, FAQ, scheduling, escalation)

## Agents

### 1. Supervisor Agent (`supervisor.py`)
**Responsibility:** Intent classification and routing

**Features:**
- Classifies user intent (greeting, faq, schedule, reschedule, cancel, escalate)
- Routes to appropriate functional agent
- Detects conversation loops (same agent 3+ times)
- Triggers escalation when stuck

**Requirements:** 1.4, 6.1

**Usage:**
```python
from agents import create_supervisor_agent
from config.settings import settings

supervisor = create_supervisor_agent(settings.get_llm_config())
result = await supervisor.classify_intent(
    message="Quero agendar depilação a laser",
    conversation_id="conv_123"
)
# Returns: {"intent": "schedule", "agent": "scheduler", ...}
```

### 2. Intake Agent (`intake.py`)
**Responsibility:** Welcome patients, understand their needs, and route without collecting personal data

**Features:**
- Greets patients warmly e identifica rapidamente o objetivo do contato
- Oferece orientações iniciais e sugere próximos passos (FAQ, Scheduler ou equipe humana)
- Finaliza acolhidas retornando explicitamente `INTAKE_COMPLETE`
- Respeita a política de não solicitar ou registrar informações pessoais

**Tools:** Nenhuma (todas as interações com dados de contato foram desativadas)

**Requirements:** 1.2, 1.3

**Usage:**
```python
from agents import create_intake_agent

intake = create_intake_agent(settings.get_llm_config())
result = await intake.process_message(
    message="Meu nome é João Silva",
    phone="+5511999999999"
)
# Returns: {"response": "...", "status": "complete", "contact_id": None}
```

### 3. FAQ Agent (`faq.py`)
**Responsibility:** Answer questions about treatments, prices, policies

**Features:**
- Searches knowledge base
- Uses message templates
- Provides treatment information
- Signals low confidence when uncertain
- Prefers Gemini 2.5 Flash for cost efficiency

**Tools:**
- `search_knowledge_base`
- `get_message_template`
- `format_template`

**Requirements:** 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 13.1-13.5

**Usage:**
```python
from agents import create_faq_agent

faq = create_faq_agent(settings.get_llm_config())
result = await faq.answer_question(
    question="Quanto custa a depilação a laser?",
    contact_name="João"
)
# Returns: {"answer": "...", "confidence": "high", ...}
```

### 4. Scheduler Agent (`scheduler.py`)
**Responsibility:** Manage appointments (booking, rescheduling, cancellation)

**Features:**
- Lists available time slots
- Creates bookings with validation
- Reschedules appointments
- Cancels with policy enforcement
- Requests explicit confirmation
- Prefers Grok-4-Reasoning for complex logic

**Tools:**
- `list_available_slots`
- `create_booking`
- `get_patient_bookings`
- `cancel_booking`
- `reschedule_booking`
- `check_cancellation_policy`

**Business Rules:**
- Business hours: Mon-Fri 08:30-19:00, Sat 08:30-12:00
- Minimum advance: 1 hour
- Cancellation policies: 4h (harmonization), 24h (laser)
- Max reschedules: 2 per booking
- Requires an existing contact record; conversations sem cadastro são escaladas automaticamente

**Requirements:** 2.1-2.7, 3.1-3.3

**Usage:**
```python
from agents import create_scheduler_agent

scheduler = create_scheduler_agent(settings.get_llm_config())
result = await scheduler.process_scheduling_request(
    message="Quero agendar para amanhã às 14h",
    contact_id="uuid",
    phone="+5511999999999",
    conversation_id="conv_123"
)
# Returns: {"response": "...", "action": "booking_created", ...}
```

### 5. Escalation Agent (`escalation.py`)
**Responsibility:** Prepare handoffs to human agents

**Features:**
- Detects escalation triggers
- Prepares conversation summaries
- Communicates handoff to patient
- Marks conversation for human takeover

**Escalation Triggers:**
- 3+ consecutive failures (loop detection)
- Explicit patient request
- Low confidence responses
- Complex situations
- Complaints

**Requirements:** 6.1-6.5

**Usage:**
```python
from agents import create_escalation_agent

escalation = create_escalation_agent(settings.get_llm_config())

# Detect trigger
trigger = await escalation.detect_escalation_trigger(
    message="Quero falar com alguém",
    routing_history=["faq", "faq", "faq"],
    confidence="low"
)

# Prepare escalation
if trigger["should_escalate"]:
    result = await escalation.prepare_escalation(
        reason=trigger["reason"],
        conversation_id="conv_123",
        contact_info={"name": "João", "phone": "+5511999999999"},
        context=conversation_history,
        priority=trigger["priority"]
    )
    # Returns: {"summary": "...", "patient_message": "...", ...}
```

## Agent Communication Flow

```
User Message
    ↓
Supervisor Agent (classify intent)
    ↓
    ├─→ Intake Agent (if greeting/new user)
    ├─→ FAQ Agent (if question)
    ├─→ Scheduler Agent (if booking/reschedule/cancel)
    └─→ Escalation Agent (if stuck/request)
    ↓
Response to User
```

## LLM Provider Strategy

- **Supervisor:** Uses configured provider (xai or gemini)
- **Intake:** Uses configured provider
- **FAQ:** Uses configured provider (recommended: Gemini 2.5 Flash)
- **Scheduler:** Uses configured provider (recommended: Gemini 2.5 Flash; Grok optional for complex logic)
- **Escalation:** Uses configured provider

## Configuration

All agents are initialized with LLM configuration from `config/settings.py`:

```python
from config.settings import settings

llm_config = settings.get_llm_config()
# Returns: {"provider": "xai", "api_key": "...", "model": "grok-4-reasoning", ...}
```

## Error Handling

All agents implement error handling:
- Catch exceptions during processing
- Return fallback responses
- Log errors for monitoring
- Trigger escalation on critical errors

## Testing

Each agent can be tested independently:

```python
# Test supervisor
result = await supervisor.classify_intent("Olá", "conv_123")
assert result["agent"] == "intake"

# Test intake
result = await intake.process_message("João Silva", "+5511999999999")
assert result["status"] == "complete"

# Test FAQ
result = await faq.answer_question("Quanto custa?")
assert result["confidence"] in ["high", "low"]

# Test scheduler
result = await scheduler.process_scheduling_request(
    "Quero agendar", "contact_id", "+5511999999999"
)
assert result["action"] in ["slots_listed", "booking_created", ...]

# Test escalation
trigger = await escalation.detect_escalation_trigger(
    "Quero falar com alguém", [], "high"
)
assert trigger["should_escalate"] == True
```

## Next Steps

After implementing agents, the next tasks are:
1. **FastAPI Gateway** (Task 6) - Webhook handling and orchestration
2. **Agent Orchestrator** (Task 6.3) - Coordinate agent execution
3. **Message Sender** (Task 6.4) - Send responses via Chatwoot
4. **Seed Data** (Task 7) - Populate knowledge base and templates

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Design Document](../.kiro/specs/multi-agent-scheduling/design.md)
- [Requirements Document](../.kiro/specs/multi-agent-scheduling/requirements.md)
- [Tasks Document](../.kiro/specs/multi-agent-scheduling/tasks.md)
