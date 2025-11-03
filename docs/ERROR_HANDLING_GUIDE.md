# Error Handling Guide

Este documento descreve o sistema de tratamento de erros implementado para o sistema de atendimento multi-agente da Clínica Luana.

## Visão Geral

O sistema de tratamento de erros é composto por três módulos principais:

1. **error_handlers.py** - Retry logic e fallback responses
2. **graceful_degradation.py** - Estratégias de degradação graciosa
3. **validators.py** - Validação e sanitização de entrada

## 1. Error Handlers (`utils/error_handlers.py`)

### Retry Logic

#### Decoradores de Retry

O módulo fornece decoradores síncronos e assíncronos para retry com backoff exponencial:

```python
from utils.error_handlers import (
    retry_with_backoff,
    async_retry_with_backoff,
    retry_chatwoot,
    retry_supabase
)

# Retry genérico síncrono com backoff exponencial
@retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
def my_function():
    # Código que pode falhar
    pass

# Retry genérico assíncrono
@async_retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
async def my_async_function():
    # Código assíncrono que pode falhar
    pass

# Retry específico para Chatwoot (3 tentativas, HTTPStatusError, RequestError, TimeoutException)
@retry_chatwoot
def send_message_to_chatwoot():
    # Chamada à API do Chatwoot
    pass

# Retry específico para Supabase (3 tentativas, ConnectionError, TimeoutError, Exception)
@retry_supabase
def query_database():
    # Operação no Supabase
    pass
```

**Características:**
- Backoff exponencial: delay × backoff_factor após cada tentativa
- Logging estruturado de tentativas e falhas
- Suporte para especificar exceções específicas para retry
- Versões síncronas e assíncronas disponíveis

### Timeout para LLM

O módulo fornece decoradores e handlers para timeouts de LLM:

```python
from utils.error_handlers import (
    timeout_llm_call,
    async_timeout_llm_call,
    LLMTimeoutHandler
)

# Decorator síncrono para timeout
@timeout_llm_call(timeout_seconds=10)
def call_gemini():
    # Chamada ao Gemini
    pass

# Decorator assíncrono para timeout
@async_timeout_llm_call(timeout_seconds=15)
async def call_grok():
    # Chamada ao Grok
    pass

# Obter timeout apropriado para o provider
timeout = LLMTimeoutHandler.get_timeout("gemini")  # 10 segundos
timeout = LLMTimeoutHandler.get_timeout("xai")     # 15 segundos
timeout = LLMTimeoutHandler.get_timeout("grok")    # 15 segundos

# Tratar timeout e obter resposta fallback
fallback_response = LLMTimeoutHandler.handle_timeout(
    provider="gemini",
    conversation_id="conv_123"
)
# Retorna: "Estou processando sua solicitação, um momento por favor..."
```

**Timeouts por Provider:**
- Gemini: 10 segundos
- Grok/xAI: 15 segundos
- Desconhecido: 15 segundos (default)

### Fallback Responses

```python
from utils.error_handlers import ErrorType, get_fallback_response

# Obter resposta fallback para um tipo de erro
response = get_fallback_response(ErrorType.SYSTEM_BUSY)
# "Desculpe, estou com alta demanda no momento..."

# Com variáveis de template
response = get_fallback_response(
    ErrorType.NO_SLOTS,
    service="Depilação a Laser",
    date_range="próxima semana",
    next_slot="15/10 às 14:00"
)
```

### Tipos de Erro Disponíveis

- `SYSTEM_BUSY` - Sistema com alta demanda
- `SERVICE_UNAVAILABLE` - Serviço indisponível
- `UNCLEAR_REQUEST` - Solicitação não compreendida
- `NO_SLOTS` - Sem horários disponíveis
- `POLICY_VIOLATION` - Violação de política
- `LLM_TIMEOUT` - Timeout do LLM
- `CHATWOOT_ERROR` - Erro na API do Chatwoot
- `SUPABASE_ERROR` - Erro no Supabase
- `REDIS_ERROR` - Erro no Redis
- `UNKNOWN_ERROR` - Erro desconhecido

### Service Error Handlers

Handlers específicos para erros de serviços externos:

```python
from utils.error_handlers import ServiceErrorHandler

# Tratar erro do Chatwoot
fallback = ServiceErrorHandler.handle_chatwoot_error(
    error=exception,
    conversation_id="conv_123"
)
# Retorna: "Tive um problema ao enviar a mensagem. Vou tentar novamente."

# Tratar erro do Supabase (retorna None para indicar falha)
result = ServiceErrorHandler.handle_supabase_error(
    error=exception,
    operation="create_booking"
)
# Retorna: None

# Tratar erro do Redis (retorna contexto vazio)
context = ServiceErrorHandler.handle_redis_error(
    error=exception,
    conversation_id="conv_123"
)
# Retorna: []
```

### Estratégias de Recuperação

```python
from utils.error_handlers import ErrorRecoveryStrategy

# Verificar se deve escalar para humano
should_escalate = ErrorRecoveryStrategy.should_escalate(
    error_count=3,
    error_type=ErrorType.LLM_TIMEOUT
)
# Retorna: True (após 3 erros consecutivos)

# Escalação imediata para erros críticos
should_escalate = ErrorRecoveryStrategy.should_escalate(
    error_count=1,
    error_type=ErrorType.SERVICE_UNAVAILABLE
)
# Retorna: True (erro crítico)

# Obter ação de recuperação recomendada
action = ErrorRecoveryStrategy.get_recovery_action(ErrorType.REDIS_ERROR)
# Retorna: "continue_without_context"

action = ErrorRecoveryStrategy.get_recovery_action(ErrorType.LLM_TIMEOUT)
# Retorna: "use_fallback_response_and_escalate"
```

**Ações de Recuperação Disponíveis:**
- `retry_after_delay` - Tentar novamente após delay
- `escalate_to_human` - Escalar para atendente humano
- `request_clarification` - Solicitar clarificação do usuário
- `suggest_alternatives` - Sugerir alternativas
- `explain_policy_and_offer_escalation` - Explicar política e oferecer escalação
- `use_fallback_response_and_escalate` - Usar resposta fallback e escalar
- `retry_with_backoff` - Retry com backoff exponencial
- `continue_without_context` - Continuar sem contexto

### Safe Execute

Decorator para executar funções com fallback em caso de erro:

```python
from utils.error_handlers import safe_execute

# Executar com valor fallback
@safe_execute(fallback_value=[], error_handler=lambda e: logger.error(str(e)))
def get_user_data():
    # Código que pode falhar
    return fetch_data()

# Se falhar, retorna []
data = get_user_data()
```

## 2. Graceful Degradation (`utils/graceful_degradation.py`)

### Gerenciador de Degradação

```python
from utils.graceful_degradation import (
    degradation_manager,
    degradation_strategy,
    ServiceStatus,
    DegradationMode
)

# Atualizar status de um serviço
degradation_manager.update_service_status("redis", ServiceStatus.UNAVAILABLE)

# Verificar modo de degradação atual
mode = degradation_manager.get_degradation_mode()
# DegradationMode.NO_CONTEXT

# Verificar se serviço está disponível
is_available = degradation_manager.is_service_available("supabase")

# Verificar se deve escalar
should_escalate = degradation_manager.should_escalate()
```

### Modos de Degradação

1. **NORMAL** - Todos os serviços funcionando
2. **NO_CONTEXT** - Redis indisponível, opera sem contexto
3. **READ_ONLY** - Supabase lento, apenas leitura
4. **FALLBACK_RESPONSES** - LLM com timeout, usa respostas pré-definidas
5. **ESCALATION_ONLY** - Múltiplos serviços down, escala tudo

### Estratégias por Serviço

#### Redis Degradation

```python
from utils.graceful_degradation import RedisGracefulDegradation

# Obter contexto vazio quando Redis está down
context = RedisGracefulDegradation.get_empty_context()

# Tratar falha de contexto
context = RedisGracefulDegradation.handle_context_failure(
    conversation_id="conv_123",
    error=redis_error
)

# Pular atualização de contexto
RedisGracefulDegradation.skip_context_update("conv_123")
```

#### Supabase Degradation

```python
from utils.graceful_degradation import SupabaseGracefulDegradation

supabase_degradation = SupabaseGracefulDegradation()

# Habilitar modo somente leitura
supabase_degradation.enable_read_only_mode()

# Verificar se pode fazer write
can_write = supabase_degradation.can_perform_write()

# Tratar falha de escrita
result = supabase_degradation.handle_write_failure(
    operation="create_booking",
    data={"service_id": "123"}
)
```

#### LLM Degradation

```python
from utils.graceful_degradation import LLMGracefulDegradation

# Obter resposta de timeout
response = LLMGracefulDegradation.get_timeout_response()

# Tratar timeout com escalação
response, should_escalate = LLMGracefulDegradation.handle_llm_timeout(
    conversation_id="conv_123",
    provider="gemini",
    intent="schedule"
)

# Obter fallback específico por intent
response = LLMGracefulDegradation.get_intent_specific_fallback("faq")
```

### Usando Estratégias de Degradação

```python
from utils.graceful_degradation import degradation_strategy

# Obter estratégia de contexto
context_fn = degradation_strategy.get_context_strategy("conv_123")
if context_fn:
    context = context_fn()  # Retorna contexto vazio se Redis down

# Obter estratégia de storage
can_proceed, message = degradation_strategy.get_storage_strategy("insert")
if not can_proceed:
    return message  # "Sistema em modo somente leitura..."

# Obter estratégia de resposta
use_llm, fallback = degradation_strategy.get_response_strategy("faq")
if not use_llm:
    return fallback  # Usa resposta pré-definida

# Verificar se deve pular operação
should_skip = degradation_strategy.should_skip_operation("context_update")
```

## 3. Validators (`utils/validators.py`)

### Validação de Telefone

```python
from utils.validators import PhoneValidator, validate_phone_number

# Validar formato
is_valid = PhoneValidator.validate("(11) 91234-5678")  # True

# Normalizar para formato padrão
normalized = PhoneValidator.normalize("11912345678")
# "+5511912345678"

# Extrair DDD
ddd = PhoneValidator.extract_ddd("+5511912345678")  # "11"

# Validar e normalizar em uma operação
result = validate_phone_number("(94) 99139-8585")
if result.is_valid:
    phone = result.data  # "+559499139858"
else:
    error = result.error
```

### Validação de Mensagem

```python
from utils.validators import MessageValidator, validate_message_content

# Validar tamanho
is_valid = MessageValidator.validate_length(message)

# Sanitizar conteúdo (remove scripts, etc)
sanitized = MessageValidator.sanitize(message)

# Verificar se está vazia
is_empty = MessageValidator.is_empty(message)

# Detectar prompt injection
has_injection = MessageValidator.contains_prompt_injection(message)

# Validar e sanitizar em uma operação
result = validate_message_content("Olá, gostaria de agendar")
if result.is_valid:
    clean_message = result.data
```

### Validação de Webhook

```python
from utils.validators import validate_and_sanitize_webhook

# Validar payload completo do webhook
result = validate_and_sanitize_webhook(webhook_payload)

if result.is_valid:
    validated = result.data
    conversation_id = validated.get_conversation_id()
    phone = validated.get_phone()
    content = validated.content  # Já sanitizado
    sender_name = validated.get_sender_name()
else:
    error_message = result.error
    # Retornar erro 400
```

### Sanitização de Entrada

```python
from utils.validators import InputSanitizer

# Sanitizar para LLM (adiciona prefixo "User says:")
safe_message = InputSanitizer.sanitize_for_llm(user_message)

# Sanitizar telefone
phone = InputSanitizer.sanitize_phone("(11) 91234-5678")

# Sanitizar nome
name = InputSanitizer.sanitize_name("João da Silva")

# Sanitizar email
email = InputSanitizer.sanitize_email("joao@example.com")
```

## Exemplos de Uso Integrado

### Exemplo 1: Processar Webhook com Tratamento de Erros

```python
from utils.validators import validate_and_sanitize_webhook
from utils.error_handlers import retry_chatwoot, ErrorType, get_fallback_response
from utils.graceful_degradation import degradation_manager, ServiceStatus

@app.post("/webhook/chatwoot")
async def handle_webhook(request: Request):
    # 1. Validar e sanitizar payload
    payload = await request.json()
    result = validate_and_sanitize_webhook(payload)
    
    if not result.is_valid:
        logger.error("webhook_validation_failed", error=result.error)
        return {"error": result.error}, 400
    
    validated = result.data
    conversation_id = validated.get_conversation_id()
    
    # 2. Verificar modo de degradação
    if degradation_manager.should_escalate():
        response = get_fallback_response(ErrorType.SERVICE_UNAVAILABLE)
        await send_message(conversation_id, response)
        await escalate_to_human(conversation_id)
        return {"status": "escalated"}, 200
    
    # 3. Processar com retry
    try:
        await process_message(validated)
        return {"status": "ok"}, 200
    except Exception as e:
        logger.error("message_processing_failed", error=str(e))
        return {"status": "error"}, 500
```

### Exemplo 2: Chamar LLM com Timeout

```python
import asyncio
from utils.error_handlers import (
    async_timeout_llm_call,
    LLMTimeoutHandler,
    ErrorType,
    get_fallback_response
)
from config.settings import settings

# Opção 1: Usar decorator
@async_timeout_llm_call(timeout_seconds=10)
async def call_gemini(prompt: str):
    return await llm_client.generate(prompt)

# Opção 2: Usar asyncio.wait_for manualmente
async def call_llm_with_timeout(prompt: str, conversation_id: str):
    provider = settings.model_provider
    timeout = LLMTimeoutHandler.get_timeout(provider)
    
    try:
        # Chamar LLM com timeout
        response = await asyncio.wait_for(
            llm_client.generate(prompt),
            timeout=timeout
        )
        return response
    
    except asyncio.TimeoutError:
        # Usar fallback
        fallback_response = LLMTimeoutHandler.handle_timeout(
            provider=provider,
            conversation_id=conversation_id
        )
        
        # Escalar para humano
        await escalate_to_human(conversation_id)
        
        return fallback_response
```

### Exemplo 3: Operação no Supabase com Degradação

```python
from utils.error_handlers import retry_supabase
from utils.graceful_degradation import degradation_strategy

@retry_supabase
def create_booking(booking_data: dict):
    # Verificar se pode fazer write
    can_proceed, message = degradation_strategy.get_storage_strategy("insert")
    
    if not can_proceed:
        logger.warning("booking_queued_due_to_degradation")
        return {"status": "queued", "message": message}
    
    # Criar booking normalmente
    result = supabase_ops.insert("appointments", booking_data)
    return {"status": "created", "data": result}
```

## Boas Práticas

1. **Sempre validar entrada do usuário** antes de processar
2. **Usar retry decorators** para chamadas a APIs externas
3. **Monitorar status dos serviços** e atualizar degradation_manager
4. **Logar todas as degradações** para análise posterior
5. **Escalar para humano** quando múltiplos serviços estão down
6. **Testar cenários de falha** regularmente
7. **Documentar novos tipos de erro** quando adicionados

## Monitoramento

```python
# Verificar status atual do sistema
from utils.graceful_degradation import degradation_manager

status = {
    "mode": degradation_manager.get_degradation_mode(),
    "services": degradation_manager.service_status,
    "should_escalate": degradation_manager.should_escalate()
}

logger.info("system_status", **status)
```

## Troubleshooting

### Redis Indisponível
- Sistema opera sem contexto de conversa
- Cada mensagem é tratada independentemente
- FAQ e agendamento continuam funcionando

### Supabase Lento
- Sistema entra em modo somente leitura
- FAQ continua com KB em cache
- Writes são enfileirados para retry

### LLM Timeout
- Sistema usa respostas pré-definidas
- Conversa é escalada para humano
- Logs registram timeout para análise

### Múltiplos Serviços Down
- Sistema escala todas conversas para humano
- Mensagem genérica de indisponibilidade
- Alertas são disparados automaticamente
