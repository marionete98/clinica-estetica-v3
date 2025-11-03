# Multi-Agent System Guide

## Overview

The Clínica Luana multi-agent system uses **AutoGen 0.4 AgentChat** to orchestrate specialized agents that handle different aspects of patient interactions. This guide describes each agent's role, capabilities, and decision-making process.

### AutoGen 0.4 Architecture

All agents have been migrated to AutoGen 0.4 with:
- **Async/await pattern** throughout the system
- **AssistantAgent** instead of ConversableAgent
- **Direct tool registration** via `tools=[]` parameter
- **Proper resource cleanup** with `cleanup()` methods
- **Dual provider support** (xAI Grok and Google Gemini)

See [AutoGen Migration Guide](AUTOGEN_MIGRATION_GUIDE.md) for technical details.

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chatwoot Webhook                          │
│                  (Incoming WhatsApp Message)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Supervisor Agent                            │
│  - Classifies intent                                         │
│  - Routes to appropriate agent                               │
│  - Detects loops and escalation needs                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
    ┌────────┐     ┌─────────┐    ┌──────────┐   ┌──────────┐
    │ Intake │     │   FAQ   │    │Scheduler │   │Escalation│
    │ Agent  │     │  Agent  │    │  Agent   │   │  Agent   │
    └────────┘     └─────────┘    └────┬─────┘   └──────────┘
         │               │              │              │
         └───────────────┴──────────────┴──────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Response Sent   │
              │  via Chatwoot    │
              └──────────────────┘
                         │
                         ▼
              ┌──────────────────────────────────────┐
              │      Background Jobs (APScheduler)    │
              │  - Reminder Job (every 30 min)       │
              │  - Feedback Job (daily 10:00)        │
              └──────────┬───────────────────────────┘
                         │
                         ▼
                  ┌──────────┐
                  │ Followup │
                  │  Agent   │
                  └──────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Automated Messages│
              │  via Chatwoot    │
              └──────────────────┘
```

## Agents

### 1. Supervisor Agent

**File:** `agents/supervisor.py`  
**Role:** Intent classification and routing  
**LLM:** Uses configured provider (Grok or Gemini)  
**Optimization:** English system prompt for token efficiency (~30% reduction)

#### Responsibilities

1. **Intent Classification**: Analyze incoming messages and classify into one of 6 intents
2. **Agent Routing**: Route to the appropriate specialized agent
3. **Loop Detection**: Identify when conversations are stuck
4. **Escalation Triggering**: Detect when human intervention is needed

#### Token Optimization

The Supervisor Agent uses an **English system prompt** to reduce token usage while maintaining Portuguese responses:
- System instructions in English (~30% fewer tokens)
- Examples remain in Portuguese for accurate pattern matching
- Explicit instruction to always respond in Portuguese
- No impact on routing accuracy or response quality

#### Intent Types

| Intent | Description | Routes To |
|--------|-------------|-----------|
| `greeting` | Initial greetings, first contact | Intake Agent |
| `faq` | Questions about treatments, prices, policies | FAQ Agent |
| `schedule` | Booking requests, availability queries | Scheduler Agent |
| `reschedule` | Rescheduling existing appointments | Scheduler Agent |
| `cancel` | Cancellation requests | Scheduler Agent |
| `escalate` | Complaints, frustration, explicit human requests | Escalation Agent |

#### Classification Examples

**GREETING (→ intake):**
- "Olá, bom dia!"
- "Primeira vez aqui"
- "Vim pelo Instagram"
- "Me indicaram vocês"

**FAQ (→ faq):**
- "Quanto custa a depilação a laser?"
- "Quais são as contraindicações do botox?"
- "Qual o horário de funcionamento?"
- "Vocês trabalham com Mounjaro?"
- "Tem apartamento para pós-operatório?"

**SCHEDULE (→ scheduler):**
- "Gostaria de agendar uma sessão de harmonização facial"
- "Quero ver horários disponíveis para laser"
- "Tem vaga para amanhã?"
- "Quais horários vocês têm livres?"

**RESCHEDULE (→ scheduler):**
- "Preciso remarcar meu agendamento"
- "Posso mudar o horário da minha consulta?"
- "Não vou conseguir ir amanhã, posso trocar?"

**CANCEL (→ scheduler):**
- "Quero cancelar minha consulta"
- "Preciso desmarcar"
- "Não vou poder ir, como cancelo?"

**ESCALATE (→ escalation):**
- "Quero falar com um atendente"
- "Isso não está funcionando"
- "Quero fazer uma reclamação"
- "Não entendi nada, me passa alguém"
- "Estou com um problema sério"

#### Ambiguous Case Handling

The supervisor uses prioritization rules for ambiguous cases:

1. **Question + Booking**: Route to FAQ first (answer question, then offer booking)
2. **Complaint + Cancellation**: Route to Escalation (prioritize complaint)
3. **Multiple Questions**: Route to FAQ (all informational)
4. **Existing Booking Query**: Route to Scheduler (can query bookings)

#### Escalation Detection

The supervisor escalates IMMEDIATELY when detecting:

1. **Loop Detected**: Same agent called 3+ times without progress
2. **Explicit Frustration**: "não está funcionando", "não entendo", "isso é ridículo"
3. **Human Request**: "quero falar com alguém", "me passa um atendente"
4. **Complaint**: "insatisfeito", "problema", "reclamação"
5. **Medical Urgency**: "dor", "emergência", "complicação", "reação alérgica"
6. **Complex Negotiation**: "desconto", "parcelamento especial", "condição especial"

#### Progress Signals (NOT escalation)

The supervisor recognizes normal conversation flow:
- Patient responding to agent questions
- Agent collecting necessary information
- Scheduling process in progress
- Patient confirming details

#### Decision Process

1. Analyze user message AND conversation history
2. Identify main intent based on examples
3. Check for escalation signals (frustration, loops, explicit requests)
4. Return agent name: `intake`, `faq`, `scheduler`, or `escalation`
5. Priority: **escalate > schedule > faq > greeting**
6. Be decisive - always return specific agent
7. When in doubt, prefer `faq` (safer than premature escalation)

#### Context-Aware Examples

```
Scenario 1: First Contact
Context: [First message]
Message: "Oi"
→ intake (greeting, needs data collection)

Scenario 2: After Intake
Context: [Name collected, 2 messages exchanged]
Message: "Quanto custa laser?"
→ faq (past intake, wants information)

Scenario 3: Natural Progression
Context: [FAQ answered about prices, 3 messages]
Message: "Quero agendar"
→ scheduler (natural flow: info → booking)

Scenario 4: In Progress (NOT a loop)
Context: [Scheduler asked for time, patient didn't respond, 2 attempts]
Message: "Não sei, qualquer horário"
→ scheduler (still in progress, not stuck)

Scenario 5: Loop + Frustration
Context: [Scheduler tried 3 times, patient confused]
Message: "Não estou entendendo nada"
→ escalation (loop detected + frustration)
```

---

### 2. Intake Agent

**File:** `agents/intake.py`  
**Role:** Initial contact and data collection  
**LLM:** Uses configured provider  
**Optimization:** English system prompt for token efficiency (~32% reduction)

#### Responsibilities

1. **Greet new patients** warmly and professionally
2. **Collect full name** (mandatory)
3. **Confirm phone number** (already available from WhatsApp)
4. **Request email** (optional but recommended)
5. **Register contact information** using available tools
6. **Pass control** to appropriate agent after completion

#### Token Optimization

The Intake Agent uses an **English system prompt** to reduce token usage while maintaining Portuguese responses:
- System instructions in English (~32% fewer tokens)
- Collection flow streamlined and simplified
- Tool descriptions converted to English for efficiency
- Examples remain in Portuguese for natural conversation flow
- Explicit instruction to always respond in Portuguese
- No impact on collection accuracy or user experience

#### Workflow

```
1. Receive greeting message
2. Respond warmly and ask for full name
3. Receive name and use it throughout conversation
4. Confirm phone number from WhatsApp
5. Ask for email (optional, don't force)
6. Use create_or_update_contact tool
7. Thank patient and signal completion (INTAKE_COMPLETE)
8. Ask how you can help today
```

#### Available Tools

- `create_or_update_contact`: Create/update contact information
- `get_contact_by_phone`: Check if patient already registered

#### Tone & Style

- Professional but welcoming
- Empathetic and attentive
- Clear and objective
- Natural and friendly language
- Use moderate emojis (😊, 💙, ✨)
- Always use patient's name after collecting it

---

### 3. FAQ Agent

**File:** `agents/faq.py`  
**Role:** Answer questions about treatments, prices, and policies  
**LLM:** Prefers Gemini 2.5 Flash (cost-effective)  
**Optimization:** English system prompt + data-driven approach (~60% token reduction)

#### Responsibilities

1. Answer questions about treatments
2. Provide pricing information
3. Explain policies (cancellation, no-show, payment)
4. Share contraindications and post-treatment care
5. Signal low confidence when appropriate

#### Token Optimization

The FAQ Agent uses a **dual optimization strategy** for maximum efficiency:

**1. English System Prompt** (~30% token reduction)
- System instructions in English for token efficiency
- Examples remain in Portuguese for accurate pattern matching
- Explicit instruction to always respond in Portuguese
- No impact on response quality or user experience

**2. Data-Driven Approach** (~30% additional token reduction)
- **Removed hardcoded treatment information** from prompt
- **Mandatory knowledge base search** for all questions
- Single source of truth (KB) for all clinic information
- No stale data in prompts (always uses current KB)

**Combined Result:** ~60% token reduction (2,100 → 850 tokens per request)

**Mandatory Workflow:**
```
1. ALWAYS search knowledge base first
2. Use KB results to structure response
3. Never provide information from memory
4. Signal low confidence if no KB results
5. Offer next step (booking, more info)
```

**Knowledge Base Tools:**

The FAQ agent can use either standard or Redis-cached tools:

```python
# Option 1: Standard tools (Supabase-based)
from tools.kb_tools import search_knowledge_base

# Option 2: Cached tools (Redis-optimized) - RECOMMENDED
from tools.kb_tools_cached import search_knowledge_base

# Ultra-fast search with automatic fallback
results, sources = await search_knowledge_base(
    query="depilação laser preço",
    top_k=3,
    category="treatments"
)
```

**Performance Benefits of Cached Tools:**
- 10-50ms response time (vs 200-500ms standard)
- 90-95% faster knowledge base access
- Reduced database load
- Automatic cache synchronization every 3 hours
- Graceful fallback to Supabase if Redis unavailable

#### Tools

- `search_knowledge_base(query, top_k, category)`: Search KB articles (MANDATORY for all questions)
- `get_message_template(template_name)`: Retrieve pre-defined templates
- `format_template(name, variables)`: Format template with variables

#### Caching System

The FAQ agent includes an intelligent caching system to improve response times and reduce LLM costs:

**Features:**
- **Response Caching**: Caches high-confidence responses for frequently asked questions
- **Question Normalization**: Normalizes questions for better cache hits (e.g., "quanto custa" → "preço")
- **TTL Management**: Configurable time-to-live (default: 1 hour)
- **Size Limits**: Configurable maximum cache size (default: 100 entries)
- **Hit Rate Tracking**: Monitors cache effectiveness
- **Cache Warming**: Pre-loads 15 common questions on startup

**Configuration:**
```python
faq_agent = create_faq_agent(
    llm_config=config,
    enable_cache=True,           # Enable/disable caching
    cache_ttl_seconds=3600,      # 1 hour TTL
    cache_max_size=100           # Max 100 cached responses
)
```

**Common Questions (Pre-cached):**
- "Quanto custa a depilação a laser?"
- "Qual o horário de funcionamento?"
- "Onde fica a clínica?"
- "Vocês fazem harmonização facial?"
- "Qual a política de cancelamento?"
- "Quantas sessões de laser preciso fazer?"
- "Depilação a laser dói?"
- "Quais são as contraindicações do botox?"
- "Posso fazer laser grávida?"
- "Quanto custa harmonização facial?"
- "Vocês trabalham com Mounjaro?"
- "Tem apartamento para pós-operatório?"
- "Quanto custa o apartamento?"
- "Como funciona a criolipólise?"
- "Vocês fazem preenchimento labial?"

**Cache Management:**
```python
# Get cache statistics
stats = await faq_agent.get_cache_stats()
# Returns: {
#   "size": 45,
#   "max_size": 100,
#   "hits": 120,
#   "misses": 30,
#   "hit_rate": 0.80,
#   "ttl_seconds": 3600
# }

# Clear cache
await faq_agent.clear_cache()

# Warm cache with common questions
await faq_agent.warm_cache(COMMON_FAQ_QUESTIONS)
```

**Benefits:**
- Reduced LLM API calls (lower costs)
- Faster response times for common questions
- Consistent answers for identical questions
- Automatic cleanup of expired entries

#### Knowledge Areas

1. **Treatments**: Laser hair removal, facial/body harmonization, Mounjaro, Laser Lavieen, body treatments, post-op care
2. **Pricing**: Fixed prices, consultation-based pricing, packages
3. **Policies**: Cancellation, no-show, payment, rescheduling limits
4. **Contraindications**: Medical conditions, pregnancy, medications
5. **Post-Treatment Care**: Instructions for each treatment type

#### Low Confidence Triggers

Escalate when:
1. Information not in knowledge base
2. Medical advice beyond scope
3. Complex pricing negotiations
4. Policy exceptions
5. Conflicting information
6. Patient dissatisfaction with answer
7. Multiple failed search attempts

#### Response Structure

1. Acknowledge question
2. Search knowledge base
3. Provide clear, structured answer
4. Include relevant details (price, duration, contraindications)
5. Offer next steps (booking, more questions)
6. Use appropriate emojis for warmth

---

### 4. Scheduler Agent

**File:** `agents/scheduler.py`  
**Role:** Handle bookings, rescheduling, and cancellations  
**LLM:** Uses Gemini 2.5 Flash (recommended) or Grok-4-Reasoning (optional)

#### Responsibilities

1. Check availability
2. Create bookings
3. Reschedule appointments
4. Cancel appointments
5. Enforce business rules
6. Communicate policies

#### LLM Configuration

The Scheduler Agent supports flexible LLM provider selection:

**Default (Recommended): Gemini 2.5 Flash**
- Cost-effective for scheduling logic
- Low temperature (0.1) for deterministic decisions
- Fast response times
- Suitable for rule-based operations

**Optional: Grok-4-Reasoning**
- Available for complex scheduling scenarios
- Higher reasoning capability

**Configuration:**
```python
scheduler_agent = create_scheduler_agent(
    llm_config=config
)
```

**Fallback Behavior:**
- If Gemini API key not configured, falls back to base LLM config
- Logs warning when fallback occurs
- System continues operating with configured provider

#### Tools

- `list_available_slots(service_id, date_range, duration_min)`: Find available times
- `create_booking(contact_id, service_id, start_ts, room_id, equipment_id)`: Create appointment
- `get_patient_bookings(phone)`: Query existing bookings
- `cancel_booking(booking_id, reason)`: Cancel appointment
- `reschedule_booking(booking_id, new_start_ts)`: Reschedule appointment

#### Critical Business Rules

1. **Business Hours**:
   - Monday-Friday: 08:30-19:00
   - Saturday: 08:30-12:00
   - Sunday: CLOSED

2. **Minimum Advance**: 1 hour before appointment

3. **Procedure Interval**: 10 minutes between procedures (automatic)

4. **Cancellation Policies**:
   - Harmonization: 4 hours advance
   - Laser hair removal: 24 hours advance
   - Apartment/Lipo de Papada: 48 hours advance

5. **Rescheduling Limit**: Maximum 2 reschedules per appointment

6. **No-Show Policy**: Counted as completed session

7. **Explicit Confirmation**: Required before creating booking

8. **Resource Allocation**: Automatic room and equipment assignment

#### Validation Examples

**Valid:**
- Monday 14:00 (within business hours)
- 2 hours advance (> 1 hour minimum)
- First rescheduling (< 2 limit)

**Invalid:**
- Saturday 14:00 (outside business hours)
- 30 minutes advance (< 1 hour minimum)
- Sunday (closed)
- Third rescheduling attempt (at limit)

#### Confirmation Flow

**Required phrases:**
- "Sim, confirmo"
- "Pode agendar"
- "Confirmo o horário"

**NOT acceptable:**
- "Acho que sim"
- "Talvez"
- "Vou ver"

#### Response Format

```
✅ Agendamento Confirmado!

📅 Data: Segunda, 20/10/2025
🕐 Horário: 14:00
💆 Procedimento: Harmonização Facial
📍 Local: Sala 03

Você receberá lembretes:
• 1 dia antes (18-26h antes)
• 2 horas antes

Política de cancelamento: 4h de antecedência
```

---

### 5. Escalation Agent

**File:** `agents/escalation.py`  
**Role:** Prepare handoff to human agents  
**LLM:** Uses configured provider (xAI Grok or Gemini)  
**AutoGen Version:** 0.4 (migrated October 2025)

#### Responsibilities

1. Acknowledge escalation need
2. Prepare conversation summary
3. Generate empathetic patient message
4. Pause automation
5. Detect escalation triggers

#### Interface

The Escalation Agent uses a structured interface for preparing handoffs:

```python
result = await escalation.prepare_escalation(
    reason="loop_detected",  # or "user_request", "low_confidence", etc.
    conversation_id="conv_123",
    contact_info={
        "phone": "+5594991398585",
        "name": "João Silva",
        "email": "joao@example.com",
        "id": "contact_uuid"
    },
    context=conversation_history,
    intents=["schedule", "faq"],
    actions_attempted=["Tentou agendar", "Buscou informações"],
    priority="medium"  # "low", "medium", or "high"
)
```

#### Response Format

Returns a dictionary with:
```python
{
    "summary": "Formatted summary for human agent",
    "patient_message": "Empathetic message to send to patient",
    "conversation_id": "conv_123",
    "priority": "medium",
    "should_pause_automation": True,
    "contact_info": {...},
    "timestamp": "2025-10-16T10:30:00"
}
```

#### Summary Format

```
RESUMO DE ESCALAÇÃO
===================

**Paciente:**
- Nome: [Nome]
- Telefone: [Telefone]
- Email: [Email]
- Contact ID: [UUID]

**Motivo da Escalação:**
[Loop detectado / Solicitação explícita / Baixa confiança / etc]

**Conversation ID:** [conv_id]

**Histórico da Conversa:**
[Timestamp] Paciente: [Mensagem]
[Timestamp] Sistema: [Resposta]
...

**Intenções Identificadas:**
[schedule, faq, cancel, etc]

**Ações Tentadas:**
- [Ação 1]
- [Ação 2]

**Prioridade:** [Baixa/Média/Alta]

**Data/Hora:** [DD/MM/YYYY HH:MM:SS]

**Próximos Passos Sugeridos:**
- Revisar histórico completo da conversa
- Entender necessidade específica do paciente
- Fornecer solução personalizada
- Registrar resolução no sistema
```

#### Escalation Triggers

The agent can detect escalation triggers automatically:

```python
trigger_check = await escalation.detect_escalation_trigger(
    message="Quero falar com alguém",
    routing_history=["faq", "faq", "faq"],
    confidence="low"
)
# Returns: {
#   "should_escalate": True,
#   "reason": "Paciente solicitou atendimento humano",
#   "priority": "medium",
#   "triggers": {
#     "explicit_request": True,
#     "loop_detected": False,
#     "low_confidence": False
#   }
# }
```

**Trigger Types:**
1. **Explicit Request**: Patient asks for human agent
2. **Loop Detected**: Same agent called 3+ times without progress
3. **Low Confidence**: Agent lacks information to respond

#### Patient Messages

The agent generates empathetic messages using the LLM:
- Brief (2-3 sentences)
- Empathetic and positive
- Thanks patient for patience
- Informs specialist will contact soon
- Uses appropriate emojis (💙, 🤝, ✨)

**Examples:**
- "Entendo! Vou conectar você com nossa equipe especializada. Um momento... 🤝"
- "Peço desculpas pela dificuldade. Nossa equipe terá mais recursos para resolver. 💙"
- "Sua situação requer análise detalhada. Vou transferir para especialista. ✨"

---

### 6. Followup Agent

**File:** `agents/followup.py`  
**Role:** Send automated messages (confirmations, reminders, feedback)  
**LLM:** Uses configured provider (xAI Grok or Gemini)  
**AutoGen Version:** 0.4 (migrated October 2025)

#### Responsibilities

1. **Booking Confirmations**: Send immediately after appointment creation
2. **D-1 Reminders**: Send 18-26 hours before appointment
3. **H-2 Reminders**: Send 1.5-2.5 hours before appointment
4. **Post-Treatment Feedback**: Request feedback 24h after treatment

#### Tools

- `send_chatwoot_message(conversation_id, message)`: Send message via Chatwoot API
- `get_message_template(template_name)`: Retrieve pre-defined message templates

#### Message Types

**1. Booking Confirmation**
```
✅ Agendamento Confirmado!

Olá, [Nome]! 💙

Seu agendamento foi confirmado com sucesso:

📅 Data: [Data]
⏰ Horário: [Horário]
💆 Procedimento: [Procedimento]
🏥 Sala: [Sala]

Política de Cancelamento:
[Política específica do procedimento]

Importante:
- Tolerância de atraso: máximo 10 minutos
- Traga documento com foto
```

**2. D-1 Reminder (18-26h before)**
```
📅 Lembrete de Agendamento

Olá, [Nome]! 💙

Este é um lembrete do seu agendamento amanhã:

📅 Data: [Data]
⏰ Horário: [Horário]
💆 Procedimento: [Procedimento]
🏥 Sala: [Sala]

Lembre-se:
- Chegue com 10 minutos de antecedência
- Traga documento com foto
- Em caso de imprevisto, avise com antecedência
```

**3. H-2 Reminder (1.5-2.5h before)**
```
⏰ Lembrete: Seu Agendamento é Hoje!

Olá, [Nome]! 💙

Seu agendamento é daqui a pouco:

⏰ Horário: [Horário]
💆 Procedimento: [Procedimento]

Importante:
- Tolerância de atraso: máximo 10 minutos
- Após esse prazo, pode ser necessário reagendar
```

**4. Post-Treatment Feedback (24h after)**
```
💙 Como Foi Sua Experiência?

Olá, [Nome]!

Esperamos que tenha gostado do seu tratamento de [Procedimento] conosco! ✨

Sua opinião é muito importante para nós. Como foi sua experiência?

- O que você achou do atendimento?
- O procedimento atendeu suas expectativas?
- Há algo que possamos melhorar?
```

#### Integration with Jobs

The Followup Agent is used by scheduled background jobs:

**Reminder Job** (`jobs/reminder_job.py`):
- Runs every 30 minutes
- Queries appointments in D-1 and H-2 windows
- Calls Followup Agent to send reminders
- Marks reminders as sent in database

**Feedback Job** (`jobs/feedback_job.py`):
- Runs daily at 10:00 AM
- Queries completed appointments from 24h ago
- Calls Followup Agent to request feedback
- Tracks feedback collection status

#### Usage Example

```python
from agents.followup import create_followup_agent

# Create agent
llm_config = {
    "provider": "xai",
    "model": "grok-beta",
    "api_key": settings.XAI_API_KEY
}
followup_agent = create_followup_agent(llm_config)

# Send booking confirmation
result = await followup_agent.send_booking_confirmation(
    conversation_id=123,
    contact_name="João Silva",
    appointment_date="15/10/2025",
    appointment_time="14:00",
    procedure="Depilação a Laser",
    room="Sala 1",
    cancellation_policy="Cancelamento com 24h de antecedência"
)

# Send D-1 reminder
result = await followup_agent.send_reminder_d1(
    conversation_id=123,
    contact_name="João Silva",
    appointment_date="15/10/2025",
    appointment_time="14:00",
    procedure="Depilação a Laser",
    room="Sala 1"
)

# Cleanup when done
await followup_agent.cleanup()
```

#### Tone & Style

- Professional and cordial
- Clear and objective
- Empathetic and welcoming
- Moderate emoji use (💙, ✨, 📅, ⏰)
- Concise messages
- Personalized with patient name

#### Error Handling

All send methods return a result dictionary:
```python
{
    "success": True,
    "message_id": "msg_123",
    "error": None
}
```

On failure:
```python
{
    "success": False,
    "message_id": None,
    "error": "Error message"
}
```

---

## Agent Orchestration

### Flow Example: Booking Request

```
1. User: "Quero agendar laser"
   → Supervisor classifies as "schedule"
   → Routes to Scheduler Agent

2. Scheduler: "Qual data você prefere?"
   → User: "Amanhã"
   → Scheduler checks availability

3. Scheduler: "Tenho 14:00 e 16:00 disponíveis"
   → User: "14:00"
   → Scheduler asks for confirmation

4. Scheduler: "Confirma agendamento para amanhã 14:00?"
   → User: "Sim, confirmo"
   → Scheduler creates booking

5. Scheduler: "✅ Agendamento confirmado! [details]"
   → Conversation ends
```

### Flow Example: Escalation

```
1. User: "Quanto custa laser?"
   → Supervisor → FAQ Agent
   → FAQ answers

2. User: "E harmonização?"
   → Supervisor → FAQ Agent
   → FAQ answers

3. User: "Não entendi nada, quero falar com alguém"
   → Supervisor detects explicit human request
   → Routes to Escalation Agent

4. Escalation Agent:
   → Prepares escalation with:
     - reason: "user_request"
     - contact_info: {phone, name, email, id}
     - context: last 10 messages
   → Generates empathetic patient message
   → Creates detailed summary for human agent
   → Returns should_pause_automation: True

5. Orchestrator:
   → Sends patient message via Chatwoot
   → Pauses automation for conversation
   → Human agent receives summary and takes over
```

---

## Configuration

### LLM Provider Selection

Set in `.env`:
```bash
MODEL_PROVIDER=xai  # or 'gemini'
```

### Agent-Specific Settings

```python
# config/settings.py
max_tool_calls_per_session: int = 3
response_timeout_seconds: int = 10
max_context_messages: int = 20
```

---

## Monitoring

### Agent Metrics

Track via `/metrics` endpoint:
- Intent classification accuracy
- Escalation rate
- Booking conversion rate
- Average latency per agent

### Logs

All agent interactions logged to Supabase `logs` table:
```python
{
  "conversation_id": "cw_conv_123",
  "intent": "schedule",
  "provider": "xai",
  "latency_ms": 3450,
  "tools_used": ["list_available_slots", "create_booking"],
  "success": true
}
```

---

## Best Practices

### 1. Intent Classification

- Always analyze conversation history, not just last message
- Look for escalation signals early
- Prefer FAQ over premature escalation
- Use context to understand progression

### 2. Agent Handoffs

- Pass relevant context to next agent
- Don't repeat information already collected
- Maintain conversation continuity

### 3. Error Handling

- Use graceful degradation when services fail
- Provide fallback responses
- Escalate on repeated failures

### 4. Tone and Language

- Professional but warm
- Use emojis appropriately
- Keep responses concise
- Avoid medical advice

---

## Testing

### Unit Tests

```bash
pytest tests/test_agents.py
```

### Integration Tests

```bash
pytest tests/test_agent_orchestration.py
```

### Manual Testing

Use `/chat` endpoint:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quero agendar laser", "phone": "+5594991398585"}'
```

---

## Troubleshooting

### High Escalation Rate

**Symptoms:** > 30% of conversations escalated

**Possible causes:**
- Supervisor too sensitive to frustration signals
- FAQ knowledge base gaps
- Scheduler business rules too strict

**Actions:**
1. Review escalated conversations
2. Identify common patterns
3. Update knowledge base
4. Refine supervisor prompt

### Low Booking Conversion

**Symptoms:** < 70% of schedule intents result in bookings

**Possible causes:**
- No available slots
- Confirmation flow unclear
- Business rules too restrictive

**Actions:**
1. Review failed booking attempts
2. Check slot availability
3. Simplify confirmation flow
4. Review business rules

### Intent Misclassification

**Symptoms:** Wrong agent handling conversations

**Possible causes:**
- Ambiguous user messages
- Insufficient context analysis
- Missing examples in prompt

**Actions:**
1. Review misclassified conversations
2. Add examples to supervisor prompt
3. Improve context analysis
4. Test with similar messages

---

## Future Enhancements

1. **Multi-language Support**: Add English and Spanish
2. **Voice Integration**: Support voice messages
3. **Proactive Outreach**: Agent-initiated conversations
4. **Sentiment Analysis**: Detect frustration earlier
5. **Learning Loop**: Improve prompts based on feedback

---

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Task 13: Prompt Optimization](TASK_13_PROMPT_OPTIMIZATION_SUMMARY.md)
- [Error Handling Guide](ERROR_HANDLING_GUIDE.md)
- [Observability Guide](OBSERVABILITY_IMPLEMENTATION.md)
