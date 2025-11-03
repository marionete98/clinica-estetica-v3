# Análise Comparativa: Chatwoot Configuration

## Resumo Executivo

Comparação entre a configuração do Chatwoot no **documento de referência** (sistema LangGraph em produção) e a **implementação atual** (sistema AutoGen Clínica Luana).

**Status Geral**: ⚠️ **Implementação Parcial** - Faltam recursos críticos

---

## Comparação de Recursos

### ✅ Recursos Implementados

| Recurso | Referência | Atual | Status |
|---------|-----------|-------|--------|
| **Validação de Webhook** | HMAC SHA256 | HMAC SHA256 | ✅ Implementado |
| **Rate Limiting** | 100 req/min | 100 req/min | ✅ Implementado |
| **Retry Logic** | 3 tentativas | 3 tentativas | ✅ Implementado |
| **Background Processing** | Sim | Sim | ✅ Implementado |
| **Envio de Mensagens** | API v1 | API v1 | ✅ Implementado |
| **Labels** | Sim | Sim | ✅ Implementado |
| **Notas Privadas** | Sim | Sim (via private=True) | ✅ Implementado |
| **Atribuição de Agente** | Sim | Sim | ✅ Implementado |
| **Status da Conversa** | Sim | Sim | ✅ Implementado |

### ❌ Recursos Ausentes (Críticos)

| Recurso | Referência | Atual | Impacto |
|---------|-----------|-------|---------|
| **Deduplicação de Mensagens** | Cache 5min | ❌ Não implementado | 🔴 ALTO - Mensagens duplicadas |
| **Message Batching** | Delay 7s | ❌ Não implementado | 🔴 ALTO - Múltiplas respostas |
| **Filtro de Mensagens Privadas** | Sim | ❌ Não implementado | 🟡 MÉDIO - Processa notas internas |
| **Verificação de Atendimento Humano** | Sim | ❌ Não implementado | 🔴 ALTO - IA interfere com humano |
| **Endpoint de Teste** | `/test/webhook` | ❌ Não existe | 🟢 BAIXO - Facilita debug |

### 🔶 Diferenças de Implementação

| Aspecto | Referência | Atual | Observação |
|---------|-----------|-------|------------|
| **Validação de Token** | Header + Query param | Apenas Header | Menos flexível |
| **Filtro de Eventos** | Múltiplos filtros | Apenas `incoming` | Menos robusto |
| **Estrutura de Payload** | Pydantic detalhado | Pydantic básico | Menos validação |
| **Logging** | Estruturado (structlog) | Estruturado (structlog) | ✅ Equivalente |
| **Client HTTP** | httpx.Client | httpx.Client | ✅ Equivalente |

---

## Análise Detalhada

### 1. Deduplicação de Mensagens ❌

**Referência**:
```python
_processed_messages: Dict[str, datetime] = {}
_DEDUP_TTL_SECONDS = 300  # 5 minutos

def is_duplicate_message(message_id: str) -> bool:
    cutoff = datetime.now() - timedelta(seconds=_DEDUP_TTL_SECONDS)
    _processed_messages = {
        mid: ts for mid, ts in _processed_messages.items()
        if ts > cutoff
    }
    
    if message_id in _processed_messages:
        return True
    
    _processed_messages[message_id] = datetime.now()
    return False
```

**Atual**: ❌ **Não implementado**

**Problema**: Se o Chatwoot reenviar o webhook (retry), a mensagem será processada novamente, gerando respostas duplicadas.

**Solução Recomendada**: Implementar cache em memória ou Redis com TTL de 5 minutos.

---

### 2. Message Batching (Coleta de Mensagens Consecutivas) ❌

**Referência**:
```python
MESSAGE_PROCESSING_DELAY_SECONDS = 7

async def collect_and_process_messages(
    conversation_id: str,
    initial_message: PendingMessage,
    delay_seconds: int
) -> tuple[str, List[PendingMessage]]:
    _pending_messages[conversation_id].append(initial_message)
    await asyncio.sleep(delay_seconds)
    messages = _pending_messages[conversation_id].copy()
    _pending_messages[conversation_id] = []
    concatenated = "\n".join(msg.content for msg in messages)
    return concatenated, messages
```

**Atual**: ❌ **Não implementado**

**Problema**: Se o cliente enviar:
```
10:00:00 → "Olá"
10:00:02 → "Quero agendar"
10:00:04 → "Botox"
```

O sistema atual processará 3 vezes separadamente, gerando 3 respostas.

**Solução Recomendada**: Implementar delay de 7 segundos para coletar mensagens consecutivas antes de processar.

---

### 3. Filtro de Mensagens Privadas ❌

**Referência**:
```python
if message.private:
    return WebhookResponse(
        success=True,
        message="Private note ignored",
        conversation_id=str(message.conversation.get("id", ""))
    )
```

**Atual**: ❌ **Não verifica campo `private`**

**Problema**: Notas privadas de agentes humanos podem ser processadas pela IA, gerando respostas indesejadas.

**Solução Recomendada**: Adicionar validação do campo `private` no payload.

---

### 4. Verificação de Atendimento Humano ❌

**Referência**:
```python
if previous_state_data:
    temp_state = ConversationState.model_validate(previous_state_data)
    
    if temp_state.human_takeover:
        logger.info(
            f"🚫 Conversa {conversation_id} em atendimento humano "
            f"(motivo: {temp_state.human_takeover_reason}) - IA desativada"
        )
        
        await private_note(
            account_id=int(account_id),
            conversation_id=int(conversation_id),
            content=f"💬 **Nova mensagem do cliente:**\n\n{message.content}"
        )
        
        return WebhookResponse(
            success=True,
            message="Conversation under human control - AI disabled",
            conversation_id=conversation_id
        )
```

**Atual**: ❌ **Não implementado**

**Problema**: Se um agente humano assumir a conversa, a IA continuará respondendo, criando conflito.

**Solução Recomendada**: 
1. Adicionar campo `automation_paused` na tabela `sessions`
2. Verificar antes de processar mensagem
3. Se pausado, apenas notificar agente humano via nota privada

---

### 5. Validação de Token - Flexibilidade

**Referência**:
```python
def validate_webhook_token(request: Request) -> tuple[bool, Optional[str]]:
    expected_token = os.getenv("CHATWOOT_WEBHOOK_TOKEN")
    
    # Aceita token do header ou query param
    header_token = request.headers.get("api_access_token")
    query_token = request.query_params.get("token")
    provided_token = header_token or query_token
    
    if not provided_token:
        return (False, "Missing webhook token")
    
    if not secrets.compare_digest(provided_token, expected_token):
        return (False, "Invalid webhook token")
    
    return (True, None)
```

**Atual**:
```python
def validate_chatwoot_signature(payload: bytes, signature: str) -> bool:
    # Apenas valida signature do header X-Chatwoot-Signature
    expected = hmac.new(
        settings.CHATWOOT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

**Diferença**: 
- Referência aceita token via **header OU query param** (fallback)
- Atual aceita apenas **signature no header**

**Impacto**: Menor flexibilidade para testes e debug.

---

### 6. Estrutura do Payload

**Referência** (mais completo):
```python
class ChatwootWebhookPayload(BaseModel):
    event: str
    id: int
    created_at: int
    content: str
    message_type: str
    content_type: str
    private: bool  # ⚠️ Campo crítico
    sender: Dict[str, Any]
    conversation: Dict[str, Any]
    inbox: Dict[str, Any]
    account: Dict[str, Any]
```

**Atual** (básico):
```python
class ChatwootWebhookPayload(BaseModel):
    event: str
    conversation: Dict[str, Any]
    message_type: str
    content: str
    sender: Dict[str, Any]
    id: int
    created_at: int
    # ❌ Falta: private, content_type, inbox, account
```

**Problema**: Não valida campos importantes como `private` e `content_type`.

---

## Variáveis de Ambiente

### Comparação

| Variável | Referência | Atual | Status |
|----------|-----------|-------|--------|
| `CHATWOOT_BASE_URL` | ✅ | `CHATWOOT_API_URL` | ✅ (nome diferente) |
| `CHATWOOT_TOKEN` | ✅ | `CHATWOOT_API_TOKEN` | ✅ (nome diferente) |
| `CHATWOOT_ACCOUNT_ID` | ✅ | ✅ | ✅ |
| `CHATWOOT_INBOX_ID` | ✅ | ❌ | ⚠️ Não usado |
| `CHATWOOT_WEBHOOK_TOKEN` | ✅ | `CHATWOOT_WEBHOOK_SECRET` | ✅ (nome diferente) |
| `MESSAGE_DEDUP_TTL_SECONDS` | ✅ | ❌ | ❌ Não implementado |
| `MESSAGE_PROCESSING_DELAY_SECONDS` | ✅ | ❌ | ❌ Não implementado |

**Observação**: Nomes diferentes mas funcionalidade equivalente para variáveis básicas.

---

## Fluxo de Processamento

### Referência (Completo)

```
1. Cliente envia mensagem
   ↓
2. Webhook recebido
   ↓
3. ✅ Valida token (header ou query)
   ↓
4. ✅ Filtra evento (message_created)
   ↓
5. ✅ Filtra tipo (incoming)
   ↓
6. ✅ Filtra privado (private=false)
   ↓
7. ✅ Verifica deduplicação
   ↓
8. ✅ Verifica atendimento humano
   ↓
9. ✅ Aguarda delay (7s) para batching
   ↓
10. ✅ Carrega estado (Redis)
    ↓
11. ✅ Processa com LangGraph
    ↓
12. ✅ Salva estado (Redis + Supabase)
    ↓
13. ✅ Envia resposta
    ↓
14. ✅ Adiciona labels
    ↓
15. ✅ Adiciona nota privada (se escalado)
```

### Atual (Parcial)

```
1. Cliente envia mensagem
   ↓
2. Webhook recebido
   ↓
3. ✅ Valida signature
   ↓
4. ⚠️ Filtra tipo (incoming) - básico
   ↓
5. ❌ NÃO verifica deduplicação
   ↓
6. ❌ NÃO verifica atendimento humano
   ↓
7. ❌ NÃO faz batching
   ↓
8. ✅ Processa com AutoGen (background)
   ↓
9. ✅ Envia resposta
   ↓
10. ✅ Adiciona labels (se implementado)
```

**Etapas Faltantes**: 4 críticas (dedup, human takeover, batching, filtro private)

---

## Recomendações Prioritárias

### 🔴 Prioridade ALTA (Implementar Imediatamente)

1. **Deduplicação de Mensagens**
   - Implementar cache em memória com TTL de 5 minutos
   - Prevenir processamento duplicado de webhooks

2. **Message Batching**
   - Implementar delay de 7 segundos
   - Coletar mensagens consecutivas antes de processar
   - Evitar múltiplas respostas para mensagens rápidas

3. **Verificação de Atendimento Humano**
   - Adicionar campo `automation_paused` em `sessions`
   - Desabilitar IA quando humano assumir
   - Notificar agente via nota privada

### 🟡 Prioridade MÉDIA

4. **Filtro de Mensagens Privadas**
   - Adicionar campo `private` no payload model
   - Ignorar notas privadas de agentes

5. **Validação de Token Flexível**
   - Aceitar token via header OU query param
   - Facilitar testes e debug

### 🟢 Prioridade BAIXA

6. **Endpoint de Teste**
   - Criar `/test/webhook` para validar autenticação
   - Criar `/test/message` para testar processamento

7. **Payload Completo**
   - Adicionar campos: `content_type`, `inbox`, `account`
   - Melhorar validação

---

## Código de Exemplo para Implementação

### 1. Deduplicação

```python
# routes/webhooks.py
from datetime import datetime, timedelta
from typing import Dict

_processed_messages: Dict[str, datetime] = {}
_DEDUP_TTL_SECONDS = 300  # 5 minutos

def is_duplicate_message(message_id: str) -> bool:
    """Verifica se mensagem já foi processada recentemente"""
    now = datetime.now()
    cutoff = now - timedelta(seconds=_DEDUP_TTL_SECONDS)
    
    # Limpa entradas antigas
    global _processed_messages
    _processed_messages = {
        mid: ts for mid, ts in _processed_messages.items()
        if ts > cutoff
    }
    
    # Verifica duplicação
    if message_id in _processed_messages:
        logger.warning(f"⚠️ Duplicate message detected: {message_id}")
        return True
    
    # Marca como processada
    _processed_messages[message_id] = now
    return False

# No webhook endpoint:
@router.post("/chatwoot")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks):
    # ... validação ...
    
    message_id = str(payload.id)
    
    # Verifica deduplicação
    if is_duplicate_message(message_id):
        return {
            "status": "ignored",
            "reason": "duplicate_message",
            "message_id": message_id
        }
    
    # ... continua processamento ...
```

### 2. Message Batching

```python
# routes/webhooks.py
import asyncio
from typing import List
from dataclasses import dataclass

@dataclass
class PendingMessage:
    content: str
    timestamp: int
    sender: Dict[str, Any]

_pending_messages: Dict[str, List[PendingMessage]] = {}
_processing_locks: Dict[str, asyncio.Lock] = {}

MESSAGE_PROCESSING_DELAY_SECONDS = 7

async def collect_and_process_messages(
    conversation_id: str,
    initial_message: PendingMessage
) -> str:
    """Coleta mensagens durante delay e retorna texto concatenado"""
    
    # Inicializa lista se não existir
    if conversation_id not in _pending_messages:
        _pending_messages[conversation_id] = []
    
    # Adiciona mensagem inicial
    _pending_messages[conversation_id].append(initial_message)
    
    logger.info(f"⏳ Aguardando {MESSAGE_PROCESSING_DELAY_SECONDS}s para mensagens adicionais")
    
    # Aguarda delay
    await asyncio.sleep(MESSAGE_PROCESSING_DELAY_SECONDS)
    
    # Coleta todas as mensagens que chegaram
    messages = _pending_messages[conversation_id].copy()
    _pending_messages[conversation_id] = []
    
    logger.info(f"📦 Coletadas {len(messages)} mensagens consecutivas")
    
    # Concatena conteúdo
    concatenated = "\n".join(msg.content for msg in messages)
    
    return concatenated

# No webhook endpoint:
@router.post("/chatwoot")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks):
    # ... validação ...
    
    # Cria lock para conversa se não existir
    if conversation_id not in _processing_locks:
        _processing_locks[conversation_id] = asyncio.Lock()
    
    # Verifica se já está processando
    if _processing_locks[conversation_id].locked():
        # Adiciona à fila de mensagens pendentes
        pending_msg = PendingMessage(
            content=message,
            timestamp=timestamp,
            sender=payload.sender
        )
        if conversation_id not in _pending_messages:
            _pending_messages[conversation_id] = []
        _pending_messages[conversation_id].append(pending_msg)
        
        return {
            "status": "queued",
            "conversation_id": conversation_id,
            "message": "Message added to batch"
        }
    
    # Adquire lock e processa
    async with _processing_locks[conversation_id]:
        pending_msg = PendingMessage(
            content=message,
            timestamp=timestamp,
            sender=payload.sender
        )
        
        # Coleta mensagens com delay
        concatenated_message = await collect_and_process_messages(
            conversation_id,
            pending_msg
        )
        
        # Processa mensagem concatenada
        background_tasks.add_task(
            process_chatwoot_message,
            conversation_id=conversation_id,
            phone=phone,
            message=concatenated_message,  # Usa mensagem concatenada
            timestamp=timestamp,
            sender=payload.sender
        )
    
    return {
        "status": "accepted",
        "conversation_id": conversation_id,
        "message": "Message queued for processing"
    }
```

### 3. Verificação de Atendimento Humano

```python
# Adicionar campo na tabela sessions:
# ALTER TABLE sessions ADD COLUMN automation_paused BOOLEAN DEFAULT FALSE;
# ALTER TABLE sessions ADD COLUMN human_takeover_reason TEXT;

# No webhook endpoint:
async def process_chatwoot_message(
    conversation_id: str,
    phone: str,
    message: str,
    timestamp: int,
    sender: Dict[str, Any]
):
    # Carrega estado da conversa
    from config.redis_client import get_redis_client
    redis = get_redis_client()
    
    state_key = f"conversation:{conversation_id}"
    state_data = await redis.get(state_key)
    
    if state_data:
        import json
        state = json.loads(state_data)
        
        # Verifica se está em atendimento humano
        if state.get("automation_paused"):
            logger.info(
                f"🚫 Conversa {conversation_id} em atendimento humano - IA desativada"
            )
            
            # Notifica agente via nota privada
            from config.chatwoot_client import chatwoot_client
            chatwoot_client.send_message(
                conversation_id=int(conversation_id),
                content=f"💬 **Nova mensagem do cliente:**\n\n{message}",
                private=True
            )
            
            return
    
    # Continua processamento normal...
```

### 4. Filtro de Mensagens Privadas

```python
# Atualizar modelo:
class ChatwootWebhookPayload(BaseModel):
    event: str
    conversation: Dict[str, Any]
    message_type: str
    content: str
    sender: Dict[str, Any]
    id: int
    created_at: int
    private: bool = False  # ⚠️ Adicionar campo
    
    @validator('private')
    def ignore_private(cls, v):
        """Rejeitar mensagens privadas"""
        if v:
            raise ValueError('Private messages not processed')
        return v
```

---

## Conclusão

A implementação atual do Chatwoot está **funcional para casos básicos**, mas **faltam recursos críticos** para produção:

### ✅ Pontos Fortes
- Validação de signature implementada
- Rate limiting funcional
- Retry logic com backoff
- Background processing
- API client completo

### ❌ Gaps Críticos
1. **Sem deduplicação** → Risco de mensagens duplicadas
2. **Sem message batching** → Múltiplas respostas para mensagens rápidas
3. **Sem verificação de atendimento humano** → IA interfere com agentes
4. **Sem filtro de mensagens privadas** → Processa notas internas

### 📊 Score de Completude

| Categoria | Score | Status |
|-----------|-------|--------|
| Autenticação | 90% | ✅ Bom |
| Processamento | 60% | ⚠️ Parcial |
| Robustez | 40% | ❌ Insuficiente |
| Observabilidade | 80% | ✅ Bom |
| **TOTAL** | **67%** | ⚠️ **Precisa melhorias** |

### 🎯 Próximos Passos

1. Implementar deduplicação (1-2 horas)
2. Implementar message batching (2-3 horas)
3. Adicionar verificação de atendimento humano (1-2 horas)
4. Adicionar filtro de mensagens privadas (30 min)

**Tempo Total Estimado**: 5-8 horas de desenvolvimento

---

**Última Atualização**: 16 de Outubro de 2025  
**Autor**: Análise Comparativa Automática
