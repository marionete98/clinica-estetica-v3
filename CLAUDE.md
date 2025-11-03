# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Clínica Luana Multi-Agent System** - An AI-powered WhatsApp customer service system for a dermatology clinic. The system uses multiple specialized AutoGen 0.4 agents coordinated through a supervisor agent to handle patient inquiries, appointments, FAQs, and escalations.

**Tech Stack:**
- Python 3.13
- AutoGen 0.4 (modular: `autogen-agentchat`, `autogen-core`, `autogen-ext`)
- Semantic Kernel 1.18.1 (LLM integration layer)
- FastAPI for web layer
- Redis for conversation context (24h TTL)
- Supabase (PostgreSQL) for persistence
- Chatwoot for WhatsApp integration
- Agent Lightning (APO) for prompt optimization

## Common Commands

### Development

```bash
# Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn main:app --reload

# Run on custom port
uvicorn main:app --reload --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests

# Run specific test file
pytest tests/test_sk_migration.py

# Run specific test
pytest tests/test_conversations.py::test_greeting_flow

# Run integration tests
python tests/run_integration_tests.py
```

### Code Quality

```bash
# Format code (Black)
black .

# Lint (Flake8)
flake8 .

# Type checking (MyPy)
mypy .

# Sort imports
isort .
```

### Agent Lightning Training

```bash
# Train agents with APO
python scripts/train_agent_lightning.py -- \
  --dataset agent_lightning/datasets/support_tasks.jsonl \
  --val-ratio 0.3 \
  --runners 4 \
  --beam-width 2 --branch-factor 2 --beam-rounds 2

# Run baseline evaluation
python scripts/eval_scheduler_baseline.py

# Test real execution evaluation
python scripts/test_real_execution_eval.py
```

## Architecture

### Multi-Agent System

The system follows a **supervisor-worker pattern** where a Supervisor Agent classifies intent and routes to specialized agents:

```
WhatsApp → Chatwoot → FastAPI → Agent Orchestrator
                                        ↓
                                   Supervisor (intent classification)
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ↓                   ↓                   ↓
                 Intake              FAQ              Scheduler
              (onboarding)     (knowledge base)    (appointments)
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        ↓
                            Escalation (human handoff)
```

**Agent Responsibilities:**

1. **Supervisor** (`agents/supervisor.py`) - Intent classification, routing, loop detection
2. **Intake** (`agents/intake.py`) - Initial patient data collection
3. **FAQ** (`agents/faq.py`) - Answers questions using knowledge base
4. **Scheduler** (`agents/scheduler.py`) - Manages appointments (book/reschedule/cancel)
5. **Escalation** (`agents/escalation.py`) - Prepares handoff to human agents
6. **Followup** (`agents/followup.py`) - Sends automated reminders and feedback requests

### LLM Integration via Semantic Kernel

All agents use **Semantic Kernel** as the LLM abstraction layer, wrapped with `SKChatCompletionAdapter` for AutoGen 0.4 compatibility:

- **Gemini** (via `GoogleAIChatCompletion`) - Used for FAQ and Scheduler (cost-effective)
- **xAI Grok** (via `OpenAIChatCompletion` with custom `base_url`) - Used for Supervisor, Intake, Escalation
- **OpenAI** - Supported for Agent Lightning training

**Critical:** The system uses AutoGen 0.4 modular packages (`autogen-agentchat`, `autogen-core`, `autogen-ext`), NOT the legacy `pyautogen` 0.2.x.

### Context Management

**Redis** stores conversation context with:
- 24-hour TTL
- Auto-trimming to last 20 messages
- Different context depths per agent (Supervisor: 3 msgs, FAQ: 4 msgs, Scheduler: 6 msgs, Escalation: 10 msgs)

**Supabase** provides permanent storage for:
- Appointments
- Patient contacts
- Knowledge base
- Conversation logs
- Metrics

### Agent Orchestrator Pattern

The `AgentOrchestrator` (`services/agent_orchestrator.py`) coordinates agent execution:

```python
# 1. Load context from Redis
context = await redis_client.get_context(conversation_id)

# 2. Supervisor classifies intent
classification = await supervisor.classify_intent(message, conversation_id, context)

# 3. Route to appropriate agent
if classification["agent"] == "faq":
    response = await faq.handle_faq_request(message, contact_id, context)
elif classification["agent"] == "scheduler":
    response = await scheduler.handle_schedule_request(message, contact_id, context)
# ... etc

# 4. Update context in Redis
await redis_client.update_context(conversation_id, response)
```

## Important Patterns

### Agent Creation Pattern

All agents follow this structure:

```python
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory

def _create_model_client(self):
    if provider == "gemini":
        sk_client = GoogleAIChatCompletion(...)
        prompt_settings = GoogleAIChatPromptExecutionSettings(...)
    elif provider == "xai":
        async_client = AsyncOpenAI(api_key=..., base_url="https://api.x.ai/v1")
        sk_client = OpenAIChatCompletion(ai_model_id=..., async_client=async_client)
        prompt_settings = OpenAIChatPromptExecutionSettings(...)

    return SKChatCompletionAdapter(
        sk_client,
        kernel=Kernel(memory=NullMemory()),
        prompt_settings=prompt_settings,
        model_info=ModelInfo(...)
    )
```

### Tool Integration Pattern

Tools are registered with agents using AutoGen's function calling:

```python
from autogen_agentchat.agents import AssistantAgent

agent = AssistantAgent(
    name="scheduler",
    system_message=SYSTEM_PROMPT,
    model_client=model_client,
    tools=[list_available_slots, create_booking, cancel_appointment]
)
```

Tools live in `tools/` directory:
- `scheduler_tools.py` - Appointment operations
- `reschedule_tools.py` - Rescheduling logic
- `kb_tools.py` / `kb_tools_cached.py` - Knowledge base search
- `contact_tools.py` - Patient data operations
- `calendar_api_client.py` - External calendar API integration

### Error Handling

Use centralized error handlers from `utils/error_handlers.py`:

```python
from utils.error_handlers import ErrorType, get_fallback_response, ErrorRecoveryStrategy

try:
    result = await agent.run(...)
except Exception as e:
    error_type = ErrorType.UNKNOWN_ERROR
    fallback_msg = get_fallback_response(error_type)
    should_escalate = ErrorRecoveryStrategy.should_escalate(error_count, error_type)
```

### Response Parsing

Use centralized parser from `utils/response_parser.py`:

```python
from utils.response_parser import parse_messages_from_run_result

run_result = await agent.run(task=prompt, cancellation_token=token)
response_text = parse_messages_from_run_result(run_result, "agent_name")
```

## Configuration

### Environment Variables

Required variables in `.env`:

```bash
# LLM Provider
MODEL_PROVIDER=xai  # or "gemini"

# xAI Configuration
XAI_API_KEY=your_key
XAI_MODEL=grok-4-reasoning

# Gemini Configuration
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash

# Database
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# Cache
REDIS_URL=redis://...

# Chatwoot
CHATWOOT_API_URL=your_url
CHATWOOT_API_TOKEN=your_token
CHATWOOT_ACCOUNT_ID=your_id

# Calendar API
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
```

See `.env.example` for all available configuration options.

### Agent Lightning Training

For prompt optimization using APO:

```bash
# Training LLM Provider (can differ from production)
AGENT_LIGHTNING_ENABLED=true
AGENT_LIGHTNING_TRAINING_PROVIDER=openai  # or "xai", "gemini"
AGENT_LIGHTNING_TRAINING_API_KEY=your_key
AGENT_LIGHTNING_TRAINING_MODEL=gpt-4o-mini
```

## Testing Strategy

### Test Organization

- `tests/test_sk_migration.py` - Semantic Kernel integration tests
- `tests/test_conversations.py` - End-to-end conversation flows
- `tests/test_e2e_complete.py` - Complete system tests
- `tests/test_tools.py` - Tool functionality tests
- `tests/test_orchestrator_*.py` - Orchestrator behavior tests
- `tests/test_agent_lightning_pipeline.py` - Agent Lightning integration

### Important Test Considerations

1. **Semantic Kernel Initialization**: Tests must properly initialize SK clients (see `tests/test_sk_init.py`)
2. **AutoGen 0.4 Patterns**: Use `agent.run()` with `CancellationToken`, not legacy `initiate_chat()`
3. **Async Context**: Most agent methods are async and require `pytest-asyncio`
4. **Mock External APIs**: Use `responses` library for Calendar API, mock Redis/Supabase where needed

## Deployment

### Railway Deployment

The system is production-ready for Railway:

```bash
# Deploy via CLI
railway up

# Or via GitHub (automatic on push to main/master)
git push origin main
```

Configuration in `railway.json`:
- Uses Dockerfile for build
- Health check at `/health` with 60s timeout
- Restart policy: ON_FAILURE with max 5 retries

### Docker

```bash
# Build image
docker build -t clinica-luana-ai .

# Run container
docker run -p 8000:8000 --env-file .env clinica-luana-ai
```

## Agent Lightning Workflow

Agent Lightning uses APO (Automatic Prompt Optimization) to improve agent prompts:

1. **Dataset Creation**: Add tasks to `agent_lightning/datasets/support_tasks.jsonl`
2. **Training**: Run `scripts/train_agent_lightning.py` with beam search parameters
3. **Evaluation**: Uses `expected_keywords` to calculate reward scores
4. **Integration**: Best prompts can be extracted from `trainer.best_resources`

See `docs/AGENT_LIGHTNING_RUNBOOK.md` for detailed workflow.

## Key Constraints & Policies

### Business Rules (hardcoded in system)

- **Business Hours**: Mon-Fri 08:30-19:00, Sat 08:30-12:00, Closed Sunday
- **Booking Advance**: Minimum 1 hour before appointment
- **Cancellation Policy**:
  - Harmonization: 4 hours minimum
  - Laser: 24 hours minimum
- **Max Reschedules**: 2 per booking

### Agent Behavior

- **Loop Detection**: Supervisor escalates if same agent called 3+ times
- **Escalation Triggers**: Patient frustration, explicit human request, medical urgency
- **Prompt Language**: System prompts in English (token efficiency), responses in Portuguese (BR)
- **Knowledge Base**: All FAQ data comes from Supabase KB, not hardcoded in prompts

## Documentation

Essential docs in `docs/`:

- `AGENTS_GUIDE_COMPACT.md` - Quick agent reference
- `SEMANTIC_KERNEL_MIGRATION.md` - SK migration details
- `AGENT_LIGHTNING_RUNBOOK.md` - APO training guide
- `CALENDAR_API_DOCS.md` - External API integration
- `ERROR_HANDLING_GUIDE.md` - Error handling patterns
- `RAILWAY_QUICKSTART.md` - Deployment guide

## Troubleshooting

### Common Issues

**Semantic Kernel Import Errors:**
- Ensure `semantic-kernel==1.18.1` is installed
- Check that `autogen-ext[openai,semantic-kernel]>=0.4.2` is installed

**Agent Not Responding:**
- Verify LLM API keys are configured
- Check Redis connection is active
- Review agent logs for timeout errors

**Calendar API 404 Errors:**
- Ensure `CALENDAR_API_URL` points to correct endpoint
- Verify API is deployed and healthy

**OpenAI API Parameter Errors (gpt-4o-mini):**
- Use `max_completion_tokens` instead of `max_tokens` for newer models
- See commit `717ab64` for reference fix

## Development Workflow

When modifying agents:

1. Update agent file in `agents/`
2. Run unit tests: `pytest tests/test_<agent_name>.py`
3. Run integration tests: `pytest tests/test_conversations.py`
4. Test with Agent Lightning if changing prompts: `python scripts/train_agent_lightning.py`
5. Update documentation in `docs/` if changing behavior
6. Commit with descriptive message (see git log for examples)

When adding new tools:

1. Create tool function in `tools/` with proper type hints
2. Add docstring describing parameters and return value
3. Register with appropriate agent(s)
4. Add tests in `tests/test_tools.py`
5. Update agent system prompt if tool requires special instructions
