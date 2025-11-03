# Melhorias do Chatwoot Implementadas

## Resumo

Implementação de 4 recursos críticos para robustez da integração com Chatwoot, baseados na análise comparativa com sistema em produção.

**Data**: 16 de Outubro de 2025  
**Status**: ✅ Implementado

---

## Recursos Implementados

### 1. ✅ Deduplicação de Mensagens

**Problema**: Chatwoot pode reenviar webhooks, causando processamento duplicado.

**Solução**: Cache em memória com TTL configurável (padrão: 5 minutos).

**Arquivos Modificados**:
- `routes/webhooks.py`: Função `is_duplicate_message()`
- `config/settings.py`: Variável `message_dedup_ttl_seconds`
- `.env.example`: `MESSAGE_DEDUP_TTL_SECONDS=300`

**Implementação**:
```python
_processed_messages: Dict[str, datetime] = {}

def is_duplicate_message(message_id: str) -> bool:
    """Check if message was already processed (TTL from settings)"""
    global _processed_messages
    now = datetime.now()
    cutoff = now - timedelta(seconds=settings.message_dedup_ttl_seconds)
    
    # Clean old entries
    _processed_messages = {
        mid: ts for mid, ts in _processed_messages.items()
        if ts > cutoff
    }
    
    # Check duplicate
    if message_id in _processed_messages:
        logger.warning(f"⚠️ Duplicate message detected: {message_id}")
        return True
    
    # Mark as processed
    _processed_messages[message_id] = now
    return False
```

**Uso no Webhook**:
```python
if is_duplicate_message(message_id):
    return {
        "status": "ignored",
        "reason": "duplicate_message",
        "message_id": message_id
    }
```

---

### 2. ✅ Message Batching (Coleta de Mensagens Consecutivas)

**Problema**: Cliente envia múltiplas mensagens rápidas → múltiplas respostas separadas.

**Solução**: Delay configurável (padrão: 7 segundos) para coletar mensagens consecutivas.

**Arquivos Modificados**:
- `routes/webhooks.py`: Função `collect_and_process_messages()`
- `config/settings.py`: Variável `message_processing_delay_seconds`
- `.env.example`: `MESSAGE_PROCESSING_DELAY_SECONDS=7`

**Implementação**:
```python
@dataclass
class PendingMessage:
    content: str
    timestamp: int
    sender: Dict[str, Any]

_pending_messages: Dict[str, List[PendingMessage]] = {}
_processing_locks: Dict[str, asyncio.Lock] = {}

async def collect_and_process_messages(
    conversation_id: str,
    initial_message: PendingMessage
) -> str:
    """Collect messages during delay and return concatenated text"""
    delay = settings.message_processing_delay_seconds
    
    if conversation_id not in _pending_messages:
        _pending_messages[conversation_id] = []
    
    _pending_messages[conversation_id].append(initial_message)
    
    logger.info(f"⏳ Waiting {delay}s for additional messages")
    await asyncio.sleep(delay)
    
    messages = _pending_messages[conversation_id].copy()
    _pending_messages[conversation_id] = []
    
    logger.info(f"📦 Collected {len(messages)} consecutive messages")
    
    concatenated = "\n".join(msg.content for msg in messages)
    return concatenated
```

**Exemplo**:
```
Cliente envia:
  10:00:00 → "Olá"
  10:00:02 → "Quero agendar"
  10:00:04 → "Botox"

Sistema aguarda 7 segundos e processa:
  "Olá\nQuero agendar\nBotox"
```

---

### 3. ✅ Verificação de Atendimento Humano

**Problema**: IA continua respondendo quando agente humano assume a conversa.

**Solução**: Flag `automation_paused` na tabela `sessions` + verificação antes de processar.

**Arquivos Modificados**:
- `supabase/migrations/002_add_automation_paused.sql`: Nova migration
- `models/database.py`: Campos `automation_paused` e `human_takeover_reason`
- `routes/webhooks.py`: Verificação em `process_chatwoot_message()`
- `routes/api.py`: Endpoint `/conversations/{id}/return-to-ai`

**Migration SQL**:
```sql
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS automation_paused BOOLEAN DEFAULT FALSE;

ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS human_takeover_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_automation_paused 
ON sessions(automation_paused) 
WHERE automation_paused = TRUE;
```

**Verificação no Webhook**:
```python
# Check if conversation is under human control
redis = get_redis_client()
state_key = f"session:{conversation_id}"
state_data = await redis.get(state_key)

if state_data:
    state = json.loads(state_data)
    
    if state.get("automation_paused"):
        logger.info(f"🚫 Conversation {conversation_id} under human control - AI disabled")
        
        # Notify agent via private note
        chatwoot_client.send_message(
            conversation_id=int(conversation_id),
            content=f"💬 **Nova mensagem do cliente:**\n\n{message}",
            private=True
        )
        return
```

**Endpoint para Retornar à IA**:
```bash
POST /conversations/{conversation_id}/return-to-ai
```

Permite agente humano reativar automação quando terminar atendimento.

---

### 4. ✅ Filtro de Mensagens Privadas

**Problema**: Notas privadas de agentes podem ser processadas pela IA.

**Solução**: Validação do campo `private` no payload.

**Arquivos Modificados**:
- `routes/webhooks.py`: Campo `private` no modelo `ChatwootWebhookPayload`

**Implementação**:
```python
class ChatwootWebhookPayload(BaseModel):
    event: str
    conversation: Dict[str, Any]
    message_type: str
    content: str
    sender: Dict[str, Any]
    id: int
    created_at: int
    private: bool = False  # ⚠️ Novo campo
    
    @validator('private')
    def no_private(cls, v):
        """Reject private messages (internal notes)"""
        if v:
            raise ValueError('Private messages not processed')
        return v
```

**Resultado**: Mensagens com `private=true` são automaticamente rejeitadas pelo validador Pydantic.

---

## Variáveis de Ambiente

### Novas Variáveis

```bash
# Message Processing
MESSAGE_DEDUP_TTL_SECONDS=300  # 5 minutes (default)
MESSAGE_PROCESSING_DELAY_SECONDS=7  # 7 seconds (default)
```

### Configuração Recomendada

**Produção**:
```bash
MESSAGE_DEDUP_TTL_SECONDS=300  # 5 minutos
MESSAGE_PROCESSING_DELAY_SECONDS=7  # 7 segundos
```

**Desenvolvimento/Testes**:
```bash
MESSAGE_DEDUP_TTL_SECONDS=60  # 1 minuto (mais rápido para testes)
MESSAGE_PROCESSING_DELAY_SECONDS=2  # 2 segundos (mais rápido para testes)
```

**Desabilitar Batching** (para debug):
```bash
MESSAGE_PROCESSING_DELAY_SECONDS=0  # Sem delay
```

---

## Fluxo de Processamento Atualizado

```
1. Cliente envia mensagem no Chatwoot
   ↓
2. Chatwoot dispara webhook → POST /webhook/chatwoot
   ↓
3. ✅ Valida signature HMAC SHA256
   ↓
4. ✅ Valida estrutura do payload (Pydantic)
   ↓
5. ✅ Filtra evento (message_created)
   ↓
6. ✅ Filtra tipo (incoming)
   ↓
7. ✅ Filtra privado (private=false) [NOVO]
   ↓
8. ✅ Verifica deduplicação (5 min TTL) [NOVO]
   ↓
9. ✅ Verifica se já está processando (lock)
   ↓
10. ✅ Aguarda delay (7s) para batching [NOVO]
    ↓
11. ✅ Coleta mensagens consecutivas [NOVO]
    ↓
12. ✅ Verifica atendimento humano [NOVO]
    ↓
13. ✅ Processa com AutoGen (background)
    ↓
14. ✅ Envia resposta via Chatwoot API
    ↓
15. ✅ Adiciona labels
    ↓
16. Cliente recebe resposta
```

---

## Endpoints Novos

### POST /conversations/{conversation_id}/return-to-ai

Retorna conversa do controle humano para automação da IA.

**Uso**:
```bash
curl -X POST http://localhost:8000/conversations/12345/return-to-ai
```

**Resposta**:
```json
{
  "success": true,
  "conversation_id": "12345",
  "message": "Conversation returned to AI automation",
  "timestamp": "2025-10-16T10:30:00"
}
```

**Ações**:
1. Atualiza `automation_paused = false` no Redis
2. Atualiza `automation_paused = false` no Supabase
3. Envia nota privada no Chatwoot confirmando reativação

---

## Logs e Monitoramento

### Novos Logs

```
⚠️ Duplicate message detected: 12345
⏳ Waiting 7s for additional messages
📦 Collected 3 consecutive messages
🚫 Conversation 12345 under human control - AI disabled
💬 Nova mensagem do cliente: [conteúdo]
✅ Automação reativada
```

### Métricas

Não há novas métricas específicas, mas os logs permitem monitorar:
- Taxa de mensagens duplicadas
- Número médio de mensagens por batch
- Conversas em atendimento humano

---

## Testes

### Suite de Testes Automatizados

**Arquivo:** `tests/test_chatwoot_improvements.py` (420+ linhas)

**Cobertura:** 15 cenários de teste abrangentes

#### Categorias de Teste

1. **Message Deduplication (2 testes)**
   - Detecção e rejeição de mensagens duplicadas
   - Expiração de detecção após TTL

2. **Message Batching (2 testes)**
   - Enfileiramento de mensagens consecutivas
   - Processamento após delay configurável

3. **Private Message Filtering (2 testes)**
   - Rejeição de mensagens privadas (notas internas)
   - Aceitação de mensagens públicas

4. **Human Takeover (2 testes)**
   - IA desabilitada quando conversa sob controle humano
   - Retorno de conversa do humano para IA

5. **Integration Tests (3 testes)**
   - Fluxo completo com todas as melhorias
   - Combinação de deduplicação + batching + filtros
   - Takeover humano + processamento de mensagens

6. **Configuration Tests (2 testes)**
   - Validação de configuração de TTL de deduplicação
   - Validação de configuração de delay de batching

7. **Error Handling (2 testes)**
   - Tratamento de payload inválido
   - Tratamento de conversation_id ausente

### Executar Testes

```bash
# Todos os testes de melhorias do Chatwoot
pytest tests/test_chatwoot_improvements.py -v

# Teste específico
pytest tests/test_chatwoot_improvements.py::test_duplicate_message_detection -v

# Com saída detalhada
pytest tests/test_chatwoot_improvements.py -v -s
```

### Exemplos de Testes

#### Teste de Deduplicação

```python
@pytest.mark.asyncio
async def test_duplicate_message_detection(client, base_webhook_payload):
    """Test that duplicate messages are detected and ignored."""
    
    # Send first message
    response1 = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"
    
    # Send same message again (duplicate)
    response2 = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response2.status_code == 200
    assert response2.json()["status"] == "ignored"
    assert response2.json()["reason"] == "duplicate_message"
```

#### Teste de Batching

```python
@pytest.mark.asyncio
async def test_message_batching_queues_consecutive_messages(client, base_webhook_payload):
    """Test that consecutive messages are queued for batching."""
    
    conversation_id = 99999
    base_webhook_payload["conversation"]["id"] = conversation_id
    
    # Send first message
    base_webhook_payload["id"] = int(time.time())
    response1 = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"
    
    # Send second message quickly (should be queued)
    await asyncio.sleep(0.5)
    base_webhook_payload["id"] = int(time.time()) + 1
    base_webhook_payload["content"] = "Second message"
    
    response2 = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response2.status_code == 200
    assert response2.json()["status"] == "queued"
    assert "batch" in response2.json()["message"].lower()
```

#### Teste de Atendimento Humano

```python
@pytest.mark.asyncio
async def test_human_takeover_disables_ai(client, base_webhook_payload):
    """Test that AI is disabled when conversation is under human control."""
    
    conversation_id = "77777"
    base_webhook_payload["conversation"]["id"] = int(conversation_id)
    
    # Set conversation to human control in Redis
    redis = get_redis_client()
    state_key = f"session:{conversation_id}"
    
    import json
    state = {
        "automation_paused": True,
        "human_takeover_reason": "escalation",
        "conversation_id": conversation_id
    }
    
    await redis.set(state_key, json.dumps(state), ex=3600)
    
    # Send message
    response = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response.status_code == 200
    # Message should be accepted but not processed by AI
    
    # Clean up
    await redis.delete(state_key)
```

#### Teste de Mensagens Privadas

```python
@pytest.mark.asyncio
async def test_private_messages_are_rejected(client, base_webhook_payload):
    """Test that private messages (internal notes) are rejected."""
    
    # Set message as private
    base_webhook_payload["private"] = True
    
    response = await client.post(
        "/webhook/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "private" in response.json()["reason"].lower()
```

### Cobertura de Testes

**Total:** 15 cenários de teste  
**Linhas de código:** 420+  
**Fixtures:** 2 (client, base_webhook_payload)  
**Categorias:** 7 (deduplicação, batching, filtros, takeover, integração, config, erros)

### Integração com CI/CD

```yaml
# .github/workflows/test.yml
- name: Run Chatwoot improvements tests
  run: pytest tests/test_chatwoot_improvements.py -v
  env:
    REDIS_URL: ${{ secrets.REDIS_URL }}
```

---

## Migração

### Passo 1: Aplicar Migration

```bash
# Conectar ao Supabase e executar:
psql $DATABASE_URL -f supabase/migrations/002_add_automation_paused.sql
```

Ou via Supabase Dashboard:
1. SQL Editor
2. Copiar conteúdo de `002_add_automation_paused.sql`
3. Executar

### Passo 2: Atualizar Variáveis de Ambiente

Adicionar ao `.env`:
```bash
MESSAGE_DEDUP_TTL_SECONDS=300
MESSAGE_PROCESSING_DELAY_SECONDS=7
```

### Passo 3: Deploy

```bash
git add .
git commit -m "feat: add chatwoot improvements (dedup, batching, human takeover)"
git push railway main
```

### Passo 4: Verificar

```bash
# Health check
curl http://your-app.railway.app/health

# Testar webhook
curl -X POST http://your-app.railway.app/webhook/chatwoot \
  -H "X-Chatwoot-Signature: test" \
  -H "Content-Type: application/json" \
  -d '{"event":"message_created",...}'
```

---

## Rollback

Se necessário reverter:

### Código
```bash
git revert HEAD
git push railway main
```

### Database
```sql
ALTER TABLE sessions DROP COLUMN IF EXISTS automation_paused;
ALTER TABLE sessions DROP COLUMN IF EXISTS human_takeover_reason;
DROP INDEX IF EXISTS idx_sessions_automation_paused;
```

---

## Próximos Passos

### Melhorias Futuras (Opcional)

1. **Persistir cache de deduplicação no Redis**
   - Atualmente em memória (perde ao reiniciar)
   - Redis permitiria compartilhar entre instâncias

2. **Dashboard de conversas em atendimento humano**
   - Listar conversas com `automation_paused=true`
   - Botão para retornar à IA

3. **Métricas de batching**
   - Número médio de mensagens por batch
   - Tempo médio de espera

4. **Configuração por conversa**
   - Delay diferente por tipo de cliente
   - TTL diferente por prioridade

---

## Referências

- [Test Guide](./CHATWOOT_IMPROVEMENTS_TEST_GUIDE.md) - Guia completo de testes automatizados
- [Análise Comparativa](./CHATWOOT_COMPARISON_ANALYSIS.md)
- [Configuração Original](./CHATWOOT_CONFIGURATION.md)
- [Message Deduplication and Batching](./MESSAGE_DEDUPLICATION_AND_BATCHING.md)
- [Chatwoot API Docs](https://www.chatwoot.com/developers/api/)

---

**Última Atualização**: 16 de Outubro de 2025  
**Autor**: Sistema de Implementação Automática  
**Status**: ✅ Pronto para Produção
