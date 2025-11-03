# ✅ CHECKLIST DE IMPLEMENTAÇÃO - Sistema AutoGen
## Clínica Luana Multi-Agent AI System

**Versão**: 1.0  
**Data de Início**: ___/___/2024  
**Responsável**: _____________________  
**Status**: 🔴 PENDENTE

---

## 📋 COMO USAR ESTE CHECKLIST

1. **Marque cada item** com [x] quando concluído
2. **Adicione notas** nos campos de observações
3. **Atualize o status** ao final de cada fase
4. **Documente problemas** encontrados
5. **Faça commit** após cada item crítico

---

## 🔴 FASE 1: ESTABILIZAÇÃO (CRÍTICO)
**Prazo**: 1 semana | **Esforço**: 8 horas | **Status**: 🟡 EM PROGRESSO

### 1.1 Centralize Response Parsing (2h) ✅ COMPLETE
**Responsável**: Augment Agent | **Data**: 2025-10-17

#### Tarefas
- [x] Criar `utils/response_parser.py` com `safe_parse_response()` e `parse_messages_from_run_result()`
- [x] Implementar validação robusta para todos os formatos de resposta AutoGen 0.7.x
- [x] Aplicar em `agents/supervisor.py` (removido `_parse_response()`)
- [x] Aplicar em `agents/intake.py`
- [x] Aplicar em `agents/faq.py` (removido `_parse_response()`)
- [x] Aplicar em `agents/scheduler.py` (removido `_parse_response()`, mantido structured output)
- [x] Aplicar em `agents/escalation.py`
- [x] Criar `tests/test_response_parser.py` com 28 testes abrangentes
- [x] Remover `tests/test_response_parsing.py` obsoleto

#### Testes
- [x] Teste: Parsing de TaskResult.messages (AutoGen 0.7.x)
- [x] Teste: Parsing de chat_message attribute
- [x] Teste: Parsing de content attribute
- [x] Teste: Parsing de strings diretas
- [x] Teste: Parsing de listas de mensagens
- [x] Teste: Edge cases (None, empty, whitespace, empty lists)
- [x] Teste: Type conversion (non-string content, dicts)
- [x] Teste: Fallback handling
- [x] Teste: Agent name in error messages
- [x] Teste: Unicode, multiline, very long content (10k chars)
- [x] Teste: Exception handling with fallback

#### Validação
- [x] 28 novos testes passando (test_response_parser.py)
- [x] 68 testes originais ainda passando
- [x] Total: 96 core tests passing
- [x] Sem regressões introduzidas
- [x] Documentação criada (docs/PHASE1_TASK1_COMPLETE.md)

**Observações**:
```
✅ COMPLETE - 2025-10-17
- Centralized parser eliminates ~225 lines of duplicate code
- Comprehensive error handling with agent name context
- All 5 agents successfully migrated
- 28 comprehensive tests added and passing
- See docs/PHASE1_TASK1_COMPLETE.md for full details
```

---

### 1.2 Fix Orchestrator Singleton with Dependency Injection (2h) ✅ COMPLETE
**Responsável**: Augment Agent | **Data**: 2025-10-17

#### Tarefas
- [x] Implementar dependency injection pattern
- [x] Criar `create_orchestrator()` factory function em `services/agent_orchestrator.py`
- [x] Atualizar `routes/webhooks.py` para usar DI
- [x] Remover singleton global (`_orchestrator_instance`)
- [x] Adicionar backward compatibility layer (deprecated functions)
- [x] Adicionar cleanup em `finally` block
- [x] Passar orchestrator instance para background tasks

#### Código Implementado
```python
# services/agent_orchestrator.py
async def create_orchestrator() -> AgentOrchestrator:
    """Factory function - nova instância por request."""
    logger.debug("Creating new orchestrator instance for request")
    return AgentOrchestrator()

# routes/webhooks.py
async def process_chatwoot_message(
    conversation_id: str,
    phone: str,
    message: str,
    timestamp: int,
    sender: Dict[str, Any],
    orchestrator: AgentOrchestrator  # NEW PARAMETER
):
    try:
        result = await orchestrator.orchestrate(conversation_id, phone, message)
        # ... processing ...
    finally:
        await orchestrator.cleanup()
```

#### Testes
- [x] Teste: 50 conversas simultâneas sem race condition
- [x] Teste: Routing history não cruza entre conversas (isolated instances)
- [x] Teste: Memory não cresce indefinidamente (100 iterations)
- [x] Teste: Performance não degradou (<50% degradation)
- [x] Teste: Backward compatibility (old functions still work)
- [x] Teste: Cleanup handles errors gracefully
- [x] Teste: Automatic cleanup on errors

#### Validação
- [x] 14 novos testes passando (test_orchestrator_di.py)
- [x] 106 core tests passando (no regressions)
- [x] Concurrency test: 50 concurrent conversations without race conditions
- [x] Memory test: 100 iterations without leaks
- [x] Performance test: <50% degradation under concurrent load
- [x] Backward compatibility verified
- [x] Documentação criada (docs/PHASE1_TASK2_COMPLETE.md)

**Observações**:
```
✅ COMPLETE - 2025-10-17
- Replaced singleton pattern with dependency injection factory
- Each request gets isolated orchestrator instance
- Eliminated race conditions in concurrent conversations
- Proper resource cleanup in finally block
- Backward compatibility maintained (deprecated functions)
- 14 comprehensive tests added and passing
- See docs/PHASE1_TASK2_COMPLETE.md for full details
```

---

### 1.3 Implement Resource Cleanup with Context Managers (2h) ✅ COMPLETE
**Responsável**: Augment Agent | **Data**: 2025-10-17

#### Tarefas
- [x] Fix "coroutine was never awaited" warning in `config/redis_client.py`
- [x] Implement lazy initialization pattern for Redis client
- [x] Add `ensure_initialized()` method (idempotent async initialization)
- [x] Add `close()` method for proper Redis cleanup
- [x] Update all Redis async methods to call `ensure_initialized()`
- [x] Fix `acquire_lock()` decorator from `@contextmanager` to `@asynccontextmanager`
- [x] Create `orchestrator_lifespan()` context manager in `services/agent_orchestrator.py`
- [x] Add `from contextlib import asynccontextmanager` import
- [x] Ensure cleanup happens in both success and error paths
- [x] Update `routes/webhooks.py` documentation with context manager usage examples
- [x] Create comprehensive tests in `tests/test_context_managers.py`

#### Código Implementado
```python
# config/redis_client.py - Lazy Initialization
async def ensure_initialized(self) -> None:
    """Ensure Redis client is initialized (idempotent)."""
    if self._initialized and self._client is not None:
        return

    self._client = redis.from_url(settings.redis_url, ...)
    await self._client.ping()
    self._initialized = True

async def close(self) -> None:
    """Close Redis client connection."""
    if self._client is not None:
        await self._client.close()
        self._client = None
        self._initialized = False

# services/agent_orchestrator.py - Context Manager
@asynccontextmanager
async def orchestrator_lifespan():
    """Context manager for orchestrator lifecycle."""
    orchestrator = AgentOrchestrator()
    try:
        yield orchestrator
    finally:
        await orchestrator.cleanup()

# Usage Example
async with orchestrator_lifespan() as orchestrator:
    result = await orchestrator.orchestrate(conv_id, phone, message)
# Cleanup happens automatically
```

#### Testes
- [x] Teste: Context manager creates and cleans up orchestrator
- [x] Teste: Cleanup happens on exception
- [x] Teste: Cleanup errors are handled gracefully
- [x] Teste: Multiple context managers create isolated instances
- [x] Teste: Redis client lazy initialization
- [x] Teste: Redis client ensure_initialized is idempotent
- [x] Teste: Redis client close() method
- [x] Teste: Redis client property raises before init
- [x] Teste: Redis methods auto-initialize
- [x] Teste: No memory leak with 100 iterations (warmup + growth check)
- [x] Teste: Redis cleanup releases resources
- [x] Teste: Cleanup on exception prevents leaks (50 iterations)
- [x] Teste: 20 concurrent context managers work correctly

#### Validação
- [x] 13 novos testes passando (test_context_managers.py)
- [x] 119 core tests passando (no regressions)
- [x] "Coroutine was never awaited" warning fixed
- [x] Redis client lazy initialization working
- [x] Context manager pattern implemented and tested
- [x] Memory leak tests passing (sub-linear growth)
- [x] Concurrent access tests passing (20 concurrent)
- [x] Documentation updated in routes/webhooks.py
- [x] Documentação criada (docs/PHASE1_TASK3_COMPLETE.md)

**Observações**:
```
✅ COMPLETE - 2025-10-17
- Fixed "coroutine was never awaited" warning in Redis client
- Implemented lazy initialization pattern for Redis (idempotent)
- Created orchestrator_lifespan() context manager
- Automatic cleanup in both success and error paths
- 13 comprehensive tests added and passing
- All 119 core tests still passing (no regressions)
- Memory leak prevention verified (100+ iterations)
- Concurrent access verified (20 concurrent context managers)
- See docs/PHASE1_TASK3_COMPLETE.md for full details
```

---

### 1.4 Add Input Validation with Pydantic (2h) ✅ COMPLETE
**Responsável**: Augment Agent | **Data**: 2025-10-17

#### Tarefas
- [x] Verify `phonenumbers` and `email-validator` packages are installed
- [x] Create `models/validation.py` with Pydantic models
- [x] Implement `ChatwootMessageInput` model with field validators
- [x] Implement phone validation using `phonenumbers` library (Brazilian format +55)
- [x] Implement message sanitization (remove control chars, preserve formatting)
- [x] Implement conversation_id validation (alphanumeric, hyphens, underscores)
- [x] Implement timestamp validation (positive integer)
- [x] Implement sender validation (required fields)
- [x] Create `ContactInput` model for contact information
- [x] Apply validation to webhook entry points in `routes/webhooks.py`
- [x] Add error handling for validation failures (HTTP 400)
- [x] Add structured logging for validation errors
- [x] Create comprehensive tests in `tests/test_input_validation.py`

#### Código Implementado
```python
# models/validation.py
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
import phonenumbers

class ChatwootMessageInput(BaseModel):
    conversation_id: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=4000)
    timestamp: int = Field(..., gt=0)
    sender: Dict[str, Any] = Field(...)

    @field_validator('phone')
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        parsed = phonenumbers.parse(v, "BR")
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(f"Invalid phone number: {v}")
        if parsed.country_code != 55:
            raise ValueError(f"Phone must be Brazilian (country code +55)")
        return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)

    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        # Remove control characters except newline, carriage return, tab
        sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', v)
        return sanitized.strip()

class ContactInput(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(None)
    consent: bool = Field(default=False)
```

#### Testes
- [x] Teste: Valid phone numbers (E.164, with formatting, without country code, with spaces, different DDD)
- [x] Teste: Invalid phone numbers (too short, letters, wrong country code, empty, whitespace)
- [x] Teste: Message sanitization (simple, newlines, tabs, control chars, extended control chars, whitespace, unicode, too long, empty, only control chars)
- [x] Teste: Conversation ID validation (numeric, alphanumeric, with underscore, whitespace stripping, empty, special chars, too long)
- [x] Teste: Sender validation (minimal, full, empty dict, missing id)
- [x] Teste: Timestamp validation (valid, zero, negative)
- [x] Teste: ContactInput validation (full, minimal, phone normalization, email, name sanitization)
- [x] Teste: Edge cases (exactly 4000 chars, exactly 50 chars, various Brazilian formats, mixed content, all fields valid)

#### Validação
- [x] 48 novos testes passando (test_input_validation.py)
- [x] 167 core tests passando (no regressions)
- [x] Phone validation working (Brazilian format +55, E.164 normalization)
- [x] Message sanitization working (control chars removed, formatting preserved)
- [x] Validation applied to webhook entry points (routes/webhooks.py)
- [x] HTTP 400 error responses for invalid input
- [x] Structured logging for validation errors
- [x] Pydantic V2 ConfigDict used (no deprecation warnings)
- [x] Documentação criada (docs/PHASE1_TASK4_COMPLETE.md)

**Observações**:
```
✅ COMPLETE - 2025-10-17
- Created models/validation.py with ChatwootMessageInput and ContactInput models
- Implemented phone validation using phonenumbers library (Brazilian format +55)
- Implemented message sanitization (removes control chars, preserves newlines/tabs)
- Implemented conversation_id, timestamp, and sender validation
- Applied validation to webhook entry points with HTTP 400 error handling
- 48 comprehensive tests added and passing (>90% coverage)
- All 167 core tests still passing (no regressions)
- Pydantic V2 style validators used (@field_validator, ConfigDict)
- See docs/PHASE1_TASK4_COMPLETE.md for full details
```

**Observações**:
```
____________________________________________________________________________
____________________________________________________________________________
```

---

### 📊 Status da Fase 1
- [ ] Todos os 4 fixes implementados
- [ ] Code review completo
- [ ] Testes unitários passando (>85% coverage)
- [ ] Testes E2E passando
- [ ] Testes de stress OK (50+ usuários simultâneos)
- [ ] Deploy em staging realizado
- [ ] Smoke test manual OK
- [ ] Documentação atualizada
- [ ] Changelog atualizado

**Data de Conclusão**: ___/___/2024  
**Status**: ⬜ PENDENTE | 🟡 EM PROGRESSO | 🟢 CONCLUÍDO

---

## 🟠 FASE 2: RESILIÊNCIA (ALTO)
**Prazo**: 2 semanas | **Esforço**: 12 horas | **Status**: ⬜ PENDENTE

### 2.1 Circuit Breakers (3h)
**Responsável**: _____________________ | **Data**: ___/___/2024

#### Tarefas
- [ ] Criar branch `feat/circuit-breakers`
- [ ] Instalar `pybreaker` library
- [ ] Implementar breaker para Calendar API
- [ ] Implementar breaker para Supabase
- [ ] Implementar breaker para Redis
- [ ] Criar endpoint `/health/circuit-breakers`
- [ ] Configurar alerting quando breaker abre

#### Código Sugerido
```python
# config/circuit_breakers.py
from pybreaker import CircuitBreaker

calendar_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    expected_exception=RequestError
)

@calendar_breaker
async def call_calendar_api_safe(**kwargs):
    return await call_calendar_api(**kwargs)
```

#### Testes
- [ ] Teste: Breaker fecha após 5 falhas
- [ ] Teste: Breaker reabre após timeout
- [ ] Teste: Fallback funciona quando aberto
- [ ] Teste: Health endpoint mostra estados

**Observações**:
```
____________________________________________________________________________
```

---

### 2.2 Observabilidade (4h)
**Responsável**: _____________________ | **Data**: ___/___/2024

#### Tarefas
- [ ] Criar branch `feat/observability`
- [ ] Instalar OpenTelemetry
- [ ] Configurar distributed tracing
- [ ] Adicionar request_id em todos os logs
- [ ] Criar span por agente
- [ ] Configurar Grafana dashboard
- [ ] Setup alerting básico

#### Código Sugerido
```python
# middleware/tracing.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@app.middleware("http")
async def add_tracing(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    
    with tracer.start_as_current_span("http_request") as span:
        span.set_attribute("request_id", request_id)
        response = await call_next(request)
        return response
```

#### Testes
- [ ] Teste: Request ID propagado
- [ ] Teste: Spans criados corretamente
- [ ] Teste: Métricas coletadas
- [ ] Teste: Dashboard visualiza dados

**Observações**:
```
____________________________________________________________________________
```

---

### 2.3 Rate Limiting (2h)
**Responsável**: _____________________ | **Data**: ___/___/2024

#### Tarefas
- [ ] Criar branch `feat/rate-limiting`
- [ ] Implementar token bucket para Chatwoot API
- [ ] Implementar per-user rate limiting
- [ ] Adicionar graceful degradation
- [ ] Configurar limites apropriados

#### Testes
- [ ] Teste: Rate limit bloqueia após threshold
- [ ] Teste: Rate limit reseta após período
- [ ] Teste: Resposta adequada quando limitado

**Observações**:
```
____________________________________________________________________________
```

---

### 2.4 Error Handling Unificado (3h)
**Responsável**: _____________________ | **Data**: ___/___/2024

#### Tarefas
- [ ] Criar branch `feat/unified-errors`
- [ ] Criar custom exceptions (`AgentError`, etc)
- [ ] Padronizar error responses
- [ ] Melhorar categorização de erros
- [ ] Adicionar error recovery strategies
- [ ] Documentar error codes

#### Testes
- [ ] Teste: Custom exceptions propagam corretamente
- [ ] Teste: Error responses consistentes
- [ ] Teste: Recovery strategies funcionam

**Observações**:
```
____________________________________________________________________________
```

---

### 📊 Status da Fase 2
- [ ] Todos os 4 componentes implementados
- [ ] Testes passando
- [ ] Deploy em staging
- [ ] Validação de resiliência
- [ ] Documentação atualizada

**Data de Conclusão**: ___/___/2024  
**Status**: ⬜ PENDENTE | 🟡 EM PROGRESSO | 🟢 CONCLUÍDO

---

## 🟡 FASE 3: OTIMIZAÇÃO (MÉDIO)
**Prazo**: 1 mês | **Esforço**: 20 horas | **Status**: ⬜ PENDENTE

### 3.1 Performance (8h)
- [ ] Parallel tool execution
- [ ] Context pipelining (Redis)
- [ ] LLM response streaming
- [ ] Model client pooling
- [ ] Connection pooling

**Observações**:
```
____________________________________________________________________________
```

---

### 3.2 Semantic FAQ Cache (6h)
- [ ] Implementar embeddings
- [ ] Configurar vector search (Redis)
- [ ] Migrar cache existente
- [ ] Validar hit rate improvement

**Observações**:
```
____________________________________________________________________________
```

---

### 3.3 Advanced Monitoring (6h)
- [ ] SLA tracking por agente
- [ ] Cost tracking detalhado
- [ ] Alert configuration
- [ ] A/B testing framework

**Observações**:
```
____________________________________________________________________________
```

---

### 📊 Status da Fase 3
- [ ] Otimizações implementadas
- [ ] Performance melhorou >30%
- [ ] Cache hit rate >85%
- [ ] Monitoring completo

**Data de Conclusão**: ___/___/2024  
**Status**: ⬜ PENDENTE | 🟡 EM PROGRESSO | 🟢 CONCLUÍDO

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Todos os testes passando (unit + integration + E2E)
- [ ] Code review completo
- [ ] Documentação atualizada
- [ ] Changelog preparado
- [ ] Backup do banco de dados
- [ ] Rollback plan documentado

### Staging Validation
- [ ] Deploy em staging realizado
- [ ] Smoke tests manuais OK
- [ ] Performance tests OK (50+ users)
- [ ] Stress tests OK (100+ requests/min)
- [ ] Memory leak check OK
- [ ] Security scan OK

### Production Deployment
- [ ] Deploy gradual planejado (10% → 50% → 100%)
- [ ] Monitoring ativo configurado
- [ ] Alerts configurados
- [ ] Hotfix team em standby
- [ ] Communication plan executado

### Post-Deployment
- [ ] Monitoring primeiras 24h
- [ ] Métricas coletadas e analisadas
- [ ] Feedback coletado
- [ ] Retrospective agendada
- [ ] Lições aprendidas documentadas

---

## 📈 MÉTRICAS DE ACOMPANHAMENTO

### Antes da Implementação
```
Data: ___/___/2024

Uptime:                    99.5%
P95 Latency:               15s
Error Rate:                1.2%
Concurrent Users (max):    20
FAQ Cache Hit Rate:        65%
Memory Usage (peak):       1.2GB
Monthly LLM Cost:          $305
```

### Após Fase 1 (Target)
```
Data: ___/___/2024

Uptime:                    99.7%
P95 Latency:               12s
Error Rate:                0.8%
Concurrent Users (max):    50
FAQ Cache Hit Rate:        65%
Memory Usage (peak):       800MB
Monthly LLM Cost:          $305
```

### Após Fase 2 (Target)
```
Data: ___/___/2024

Uptime:                    99.9%
P95 Latency:               10s
Error Rate:                0.5%
Concurrent Users (max):    75
FAQ Cache Hit Rate:        65%
Memory Usage (peak):       700MB
Monthly LLM Cost:          $305
```

### Após Fase 3 (Target)
```
Data: ___/___/2024

Uptime:                    99.9%
P95 Latency:               <7s
Error Rate:                <0.5%
Concurrent Users (max):    100
FAQ Cache Hit Rate:        >85%
Memory Usage (peak):       <600MB
Monthly LLM Cost:          $250
```

---

## 📞 CONTATOS E ESCALAÇÃO

### Time Técnico
- **Tech Lead**: ______________________ | Slack: @_____ | Tel: _________
- **Backend Dev**: ____________________ | Slack: @_____ | Tel: _________
- **QA Engineer**: ____________________ | Slack: @_____ | Tel: _________
- **DevOps**: _________________________ | Slack: @_____ | Tel: _________

### Escalação de Problemas
1. **Nível 1**: Dev responsável
2. **Nível 2**: Tech Lead (issues bloqueantes)
3. **Nível 3**: CTO (decisões arquiteturais)

### Canais de Comunicação
- **Daily Updates**: Slack #project-clinica-luana
- **Bloqueios**: @tech-lead no Slack
- **Emergências**: Ligar Tech Lead

---

## 📝 NOTAS E OBSERVAÇÕES GERAIS

### Problemas Encontrados
```
Data       | Problema                              | Solução              | Status
-----------+--------------------------------------+----------------------+--------
___/___    |                                      |                      | 
___/___    |                                      |                      | 
___/___    |                                      |                      | 
```

### Decisões Técnicas
```
Data       | Decisão                               | Justificativa        | Aprovado Por
-----------+--------------------------------------+----------------------+-------------
___/___    |                                      |                      | 
___/___    |                                      |                      | 
___/___    |                                      |                      | 
```

### Lições Aprendidas
```
____________________________________________________________________________
____________________________________________________________________________
____________________________________________________________________________
```

---

## ✅ SIGN-OFF FINAL

### Fase 1: Estabilização
- [ ] **Dev Lead**: _____________________ | Data: ___/___/2024
- [ ] **QA Lead**: ______________________ | Data: ___/___/2024
- [ ] **Tech Lead**: ____________________ | Data: ___/___/2024

### Fase 2: Resiliência
- [ ] **Dev Lead**: _____________________ | Data: ___/___/2024
- [ ] **QA Lead**: ______________________ | Data: ___/___/2024
- [ ] **Tech Lead**: ____________________ | Data: ___/___/2024

### Fase 3: Otimização
- [ ] **Dev Lead**: _____________________ | Data: ___/___/2024
- [ ] **QA Lead**: ______________________ | Data: ___/___/2024
- [ ] **Tech Lead**: ____________________ | Data: ___/___/2024

### Production Release
- [ ] **Tech Lead**: ____________________ | Data: ___/___/2024
- [ ] **Product Owner**: ________________ | Data: ___/___/2024
- [ ] **CTO/VP Eng**: ___________________ | Data: ___/___/2024

---

**Versão do Checklist**: 1.0  
**Última Atualização**: ___/___/2024  
**Status Geral**: 🔴 PENDENTE | 🟡 EM PROGRESSO | 🟢 CONCLUÍDO

---

*Mantenha este checklist atualizado diariamente. Faça commit após cada item concluído para tracking de progresso.*