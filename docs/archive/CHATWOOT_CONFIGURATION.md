# Configuração do Chatwoot - Documentação Completa

## Índice
1. [Visão Geral](#visão-geral)
2. [Variáveis de Ambiente](#variáveis-de-ambiente)
3. [Configuração do Webhook](#configuração-do-webhook)
4. [Autenticação e Segurança](#autenticação-e-segurança)
5. [Processamento de Mensagens](#processamento-de-mensagens)
6. [API Client](#api-client)
7. [Fluxo de Integração](#fluxo-de-integração)
8. [Testes e Validação](#testes-e-validação)

---

## Visão Geral

O sistema integra-se com o Chatwoot através de webhooks para receber mensagens de clientes e enviar respostas automatizadas. A integração é bidirecional:

- **Entrada (Webhook)**: Chatwoot → Sistema AI (mensagens dos clientes)
- **Saída (API)**: Sistema AI → Chatwoot (respostas, labels, notas privadas)

### Arquitetura da Integração

```
Cliente → Chatwoot → Webhook → Sistema AI → LangGraph → Resposta → Chatwoot API → Cliente
```

---

## Variáveis de Ambiente

### Obrigatórias

```bash
# URL base do Chatwoot (sem barra final)
CHATWOOT_BASE_URL=https://chatwoot.luanacarladermoclinic.com

# Token de API do Chatwoot
# Obter em: Settings → Profile → Access Token
CHATWOOT_TOKEN=your_chatwoot_api_token_here

# ID da conta no Chatwoot
CHATWOOT_ACCOUNT_ID=1

# ID da inbox no Chatwoot
CHATWOOT_INBOX_ID=1

# Token de validação do webhook (segurança)
# Deve ser o mesmo configurado no Chatwoot
CHATWOOT_WEBHOOK_TOKEN=your_webhook_validation_token_here
```

### Configuração no Arquivo

**Localização**: `app/config.py`

```python
# Configurações do Chatwoot
CHATWOOT_BASE_URL = os.getenv("CHATWOOT_BASE_URL", "")
CHATWOOT_TOKEN = os.getenv("CHATWOOT_TOKEN", "")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "")
CHATWOOT_INBOX_ID = os.getenv("CHATWOOT_INBOX_ID", "")
CHATWOOT_WEBHOOK_TOKEN = os.getenv("CHATWOOT_WEBHOOK_TOKEN", "")
```

---

## Configuração do Webhook

### No Painel do Chatwoot

1. **Acessar Configurações**
   - Settings → Integrations → Webhooks

2. **Criar Novo Webhook**
   - URL: `https://seu-dominio.railway.app/webhook/chatwoot`
   - Events: Selecionar `message_created`

3. **Configurar Autenticação**
   - Adicionar header customizado:
     - Key: `api_access_token`
     - Value: `seu_webhook_token_aqui`

### Endpoint do Webhook

**URL**: `POST /webhook/chatwoot`

**Headers Requeridos**:
```
api_access_token: seu_webhook_token_aqui
Content-Type: application/json
```

**Payload Esperado** (formato Chatwoot):
```json
{
  "event": "message_created",
  "id": 12345,
  "created_at": "2025-10-15T10:30:00Z",
  "content": "Olá, gostaria de agendar uma avaliação",
  "message_type": "incoming",
  "content_type": "text",
  "private": false,
  "sender": {
    "id": 1,
    "name": "João Silva",
    "type": "contact"
  },
  "conversation": {
    "id": 100,
    "inbox_id": 1,
    "status": "open"
  },
  "inbox": {
    "id": 1,
    "name": "API Inbox",
    "channel": "api"
  },
  "account": {
    "id": 1,
    "name": "Clinic Account"
  }
}
```

---

## Autenticação e Segurança

### Validação do Token

**Implementação**: `server/main.py` → `validate_webhook_token()`

```python
def validate_webhook_token(request: Request) -> tuple[bool, Optional[str]]:
    """
    Valida token de autenticação do webhook
    
    Aceita token em:
    1. Header: api_access_token (preferencial)
    2. Query param: ?token=xxx (fallback)
    
    Usa comparação constant-time para prevenir timing attacks
    """
    expected_token = os.getenv("CHATWOOT_WEBHOOK_TOKEN")
    
    # Se token não configurado, desabilita validação com warning
    if not expected_token:
        logger.warning("⚠️ CHATWOOT_WEBHOOK_TOKEN not configured")
        return (True, None)
    
    # Aceita token do header ou query param
    header_token = request.headers.get("api_access_token")
    query_token = request.query_params.get("token")
    provided_token = header_token or query_token
    
    if not provided_token:
        return (False, "Missing webhook token")
    
    # Validação constant-time
    if not secrets.compare_digest(provided_token, expected_token):
        return (False, "Invalid webhook token")
    
    return (True, None)
```

### Respostas de Segurança

| Cenário | Status Code | Resposta |
|---------|-------------|----------|
| Token válido | 200 | Processa mensagem |
| Token inválido | 401 | `{"detail": "Invalid webhook token"}` |
| Token ausente | 401 | `{"detail": "Missing webhook token"}` |
| Token não configurado | 200 | ⚠️ Processa com warning |

---

## Processamento de Mensagens

### Filtros de Eventos

O sistema aplica múltiplos filtros antes de processar mensagens:

#### 1. Filtro de Tipo de Evento

**Aceito**: `message_created`  
**Ignorado**: `message_updated`, `conversation_created`, `conversation_status_changed`, etc.

```python
if message.event != "message_created":
    return WebhookResponse(
        success=True,
        message=f"Event {message.event} ignored",
        conversation_id=str(message.conversation.get("id", ""))
    )
```

#### 2. Filtro de Tipo de Mensagem

**Aceito**: `incoming` (mensagens de clientes)  
**Ignorado**: `outgoing` (mensagens de agentes), `template` (mensagens automáticas)

```python
if message.message_type != "incoming":
    return WebhookResponse(
        success=True,
        message=f"{message.message_type.capitalize()} message ignored",
        conversation_id=str(message.conversation.get("id", ""))
    )
```

#### 3. Filtro de Mensagens Privadas

**Aceito**: `private = false` (mensagens públicas)  
**Ignorado**: `private = true` (notas privadas de agentes)

```python
if message.private:
    return WebhookResponse(
        success=True,
        message="Private note ignored",
        conversation_id=str(message.conversation.get("id", ""))
    )
```

### Deduplicação de Mensagens

**Objetivo**: Prevenir processamento duplicado se Chatwoot reenviar webhook

**Implementação**: Cache em memória com TTL de 5 minutos (300 segundos)

```python
# Cache global
_processed_messages: Dict[str, datetime] = {}
_DEDUP_TTL_SECONDS = 300  # 5 minutos

def is_duplicate_message(message_id: str) -> bool:
    """Verifica se mensagem já foi processada recentemente"""
    
    # Limpa entradas antigas
    cutoff = datetime.now() - timedelta(seconds=_DEDUP_TTL_SECONDS)
    _processed_messages = {
        mid: ts for mid, ts in _processed_messages.items()
        if ts > cutoff
    }
    
    # Verifica duplicação
    if message_id in _processed_messages:
        logger.warning(f"⚠️ Duplicate message detected: {message_id}")
        return True
    
    # Marca como processada
    _processed_messages[message_id] = datetime.now()
    return False
```

**Configuração**:
```bash
MESSAGE_DEDUP_TTL_SECONDS=300  # Padrão: 5 minutos
```

### Message Batching (Coleta de Mensagens Consecutivas)

**Objetivo**: Concatenar mensagens consecutivas do mesmo usuário antes de processar

**Delay**: 7 segundos (configurável)

**Exemplo**:
```
Cliente envia:
  10:00:00 → "Olá"
  10:00:02 → "Quero agendar"
  10:00:04 → "Botox"

Sistema aguarda 7 segundos e processa:
  "Olá\nQuero agendar\nBotox"
```

**Implementação**:

```python
# Configuração
MESSAGE_PROCESSING_DELAY_SECONDS = 7  # segundos

async def collect_and_process_messages(
    conversation_id: str,
    initial_message: PendingMessage,
    delay_seconds: int
) -> tuple[str, List[PendingMessage]]:
    """
    Coleta mensagens durante período de delay
    
    Returns:
        (texto_concatenado, lista_de_mensagens)
    """
    # Adiciona mensagem inicial
    _pending_messages[conversation_id].append(initial_message)
    
    # Aguarda delay
    await asyncio.sleep(delay_seconds)
    
    # Coleta todas as mensagens que chegaram
    messages = _pending_messages[conversation_id].copy()
    _pending_messages[conversation_id] = []
    
    # Concatena conteúdo
    concatenated = "\n".join(msg.content for msg in messages)
    
    return concatenated, messages
```

**Configuração**:
```bash
MESSAGE_PROCESSING_DELAY_SECONDS=7  # Padrão: 7 segundos
```

### Verificação de Atendimento Humano

**Objetivo**: Desabilitar IA quando conversa está em atendimento humano

```python
if previous_state_data:
    temp_state = ConversationState.model_validate(previous_state_data)
    
    if temp_state.human_takeover:
        logger.info(
            f"🚫 Conversa {conversation_id} em atendimento humano "
            f"(motivo: {temp_state.human_takeover_reason}) - IA desativada"
        )
        
        # Notifica agente sobre nova mensagem
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

---

## API Client

### Classe ChatwootAPI

**Localização**: `app/tools/chatwoot.py`

**Inicialização**:
```python
from app.tools.chatwoot import ChatwootAPI

client = ChatwootAPI(
    base_url="https://chatwoot.example.com",
    token="your_api_token",
    account_id="1"
)
```

### Métodos Disponíveis

#### 1. Enviar Mensagem

```python
await client.send_message(
    conversation_id=100,
    content="Olá! Como posso ajudar?",
    message_type="outgoing",  # ou "template"
    private=False  # True para nota privada
)
```

**Endpoint**: `POST /api/v1/accounts/{account_id}/conversations/{conversation_id}/messages`

**Payload**:
```json
{
  "content": "Olá! Como posso ajudar?",
  "message_type": "outgoing",
  "private": false
}
```

#### 2. Adicionar Label

```python
await client.add_label(
    conversation_id=100,
    label="FAQ"
)
```

**Endpoint**: `POST /api/v1/accounts/{account_id}/conversations/{conversation_id}/labels`

**Payload**:
```json
{
  "labels": ["FAQ"]
}
```

**Mapeamento de Intenções → Labels**:
```python
intent_label_map = {
    "FAQ_ESTETICA": "FAQ",
    "AGENDAR_AVALIACAO": "AGENDAMENTO",
    "AGENDAR_PROCEDIMENTO": "AGENDAMENTO",
    "LEAD_COMERCIAL": "LEAD",
    "FOLLOWUP": "FOLLOWUP",
    "HUMANO": "HUMANO"
}
```

#### 3. Adicionar Nota Privada

```python
await client.private_note(
    conversation_id=100,
    content="Cliente interessado em Botox. Confiança: 0.85"
)
```

**Nota**: Internamente chama `send_message()` com `private=True`

#### 4. Atribuir Agente

```python
# Atribuir agente
await client.assign_agent(
    conversation_id=100,
    agent_id=5
)

# Remover atribuição
await client.assign_agent(
    conversation_id=100,
    agent_id=None
)
```

**Endpoint**: `POST /api/v1/accounts/{account_id}/conversations/{conversation_id}/assignments`

#### 5. Atualizar Status da Conversa

```python
await client.update_conversation_status(
    conversation_id=100,
    status="resolved"  # ou "open", "pending"
)
```

**Endpoint**: `POST /api/v1/accounts/{account_id}/conversations/{conversation_id}/toggle_status`

#### 6. Obter Detalhes da Conversa

```python
conversation = await client.get_conversation(conversation_id=100)
```

**Endpoint**: `GET /api/v1/accounts/{account_id}/conversations/{conversation_id}`

#### 7. Obter Detalhes do Contato

```python
contact = await client.get_contact(contact_id=1)
```

**Endpoint**: `GET /api/v1/accounts/{account_id}/contacts/{contact_id}`

#### 8. Atualizar Atributos do Contato

```python
await client.update_contact_attributes(
    contact_id=1,
    attributes={
        "lead_score": 85,
        "interested_in": "Botox",
        "budget": "R$ 1000-2000"
    }
)
```

**Endpoint**: `PUT /api/v1/accounts/{account_id}/contacts/{contact_id}`

#### 9. Obter Mensagens da Conversa

```python
messages = await client.get_conversation_messages(
    conversation_id=100,
    limit=50
)
```

**Endpoint**: `GET /api/v1/accounts/{account_id}/conversations/{conversation_id}/messages`

### Tratamento de Erros

Todos os métodos retornam dicionário com estrutura consistente:

**Sucesso**:
```python
{
    "id": 123,
    "content": "Mensagem enviada",
    # ... outros campos da resposta
}
```

**Erro HTTP**:
```python
{
    "error": "http_error",
    "status": 500,
    "message": "Internal Server Error"
}
```

**Timeout**:
```python
{
    "error": "timeout_error",
    "message": "Request timed out"
}
```

**Erro Geral**:
```python
{
    "error": "general_error",
    "message": "Connection refused"
}
```

### Health Check

```python
from app.tools.chatwoot import health_check

status = await health_check()
```

**Resposta**:
```python
{
    "chatwoot_available": True,
    "account_id": "1",
    "base_url": "https://chatwoot.example.com",
    "status": "healthy"
}
```

---

## Fluxo de Integração

### Fluxo Completo de Processamento

```
1. Cliente envia mensagem no Chatwoot
   ↓
2. Chatwoot dispara webhook → POST /webhook/chatwoot
   ↓
3. Sistema valida token de autenticação
   ↓
4. Sistema aplica filtros (event type, message type, private)
   ↓
5. Sistema verifica deduplicação
   ↓
6. Sistema verifica se conversa está em atendimento humano
   ↓
7. Sistema aguarda delay para coletar mensagens consecutivas (7s)
   ↓
8. Sistema carrega estado anterior da conversa (Redis)
   ↓
9. Sistema processa mensagem através do LangGraph
   ↓
10. Sistema salva estado atualizado (Redis + Supabase)
    ↓
11. Sistema envia resposta via API do Chatwoot
    ↓
12. Sistema adiciona labels baseados na intenção
    ↓
13. Sistema adiciona nota privada se houver escalonamento
    ↓
14. Cliente recebe resposta no Chatwoot
```

### Processamento em Background

Para não bloquear o webhook, operações pesadas são executadas em background:

```python
# Retorna resposta imediata
return WebhookResponse(
    success=True,
    message="Mensagem processada com sucesso",
    conversation_id=conversation_id
)

# Processa em background
background_tasks.add_task(
    process_conversation_result,
    result_state,
    account_id,
    conversation_id
)
```

**Tarefas em Background**:
1. Salvar estado em Redis
2. Arquivar em Supabase
3. Enviar resposta para Chatwoot
4. Adicionar labels
5. Adicionar notas privadas

### Mensagem de Fallback

Se envio da resposta falhar, sistema tenta enviar mensagem de fallback:

```python
try:
    await send_message(account_id, conversation_id, state.response_text)
except Exception as e:
    logger.error(f"Erro ao enviar resposta: {e}")
    
    # Fallback
    fallback_msg = (
        "Obrigado pelo contato! Nossa equipe irá responder em breve. "
        "Para atendimento imediato: (94) 99139-8585"
    )
    await send_message(account_id, conversation_id, fallback_msg)
```

---

## Testes e Validação

### Testes Automatizados

**Localização**: `tests/test_chatwoot_integration_complete.py`

**Cobertura**:
- ✅ Validação de token (header e query param)
- ✅ Filtros de eventos e tipos de mensagem
- ✅ Deduplicação de mensagens
- ✅ Message batching e delay
- ✅ Envio de mensagens
- ✅ Adição de labels
- ✅ Notas privadas
- ✅ Tratamento de erros
- ✅ Health check

**Executar Testes**:
```bash
# Todos os testes
pytest tests/test_chatwoot_integration_complete.py -v

# Teste específico
pytest tests/test_chatwoot_integration_complete.py::TestWebhookTokenValidation -v

# Com cobertura
pytest tests/test_chatwoot_integration_complete.py --cov=app.tools.chatwoot --cov-report=html
```

### Endpoint de Teste

**URL**: `POST /test/webhook`

**Uso**: Validar autenticação do webhook

```bash
curl -X POST http://localhost:8000/test/webhook \
  -H "api_access_token: seu_token_aqui" \
  -H "Content-Type: application/json"
```

**Resposta Sucesso**:
```json
{
  "success": true,
  "message": "✅ Autenticação do webhook validada com sucesso!"
}
```

**Resposta Erro**:
```json
{
  "success": false,
  "message": "❌ Token inválido"
}
```

### Teste Manual de Mensagem

**URL**: `POST /test/message`

**Payload**:
```json
{
  "message": "Quero agendar uma avaliação de Botox"
}
```

**Resposta**:
```json
{
  "success": true,
  "message": "Mensagem de teste processada",
  "conversation_id": "test_1729000000",
  "intent": "AGENDAR_AVALIACAO",
  "response_text": "Ótimo! Vou te ajudar a agendar..."
}
```

### Validação de Health Check

```bash
curl http://localhost:8000/health
```

**Resposta**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:30:00",
  "version": "1.0.0",
  "environment": "production"
}
```

### Logs de Monitoramento

**Eventos Importantes**:

```
✅ Webhook token validated
📥 Webhook received - Event: message_created
⏳ Aguardando 7 segundos para mensagens adicionais
📦 Coletadas 3 mensagens consecutivas
📝 Processando mensagens concatenadas
🚫 Conversa em atendimento humano - IA desativada
⚠️ Duplicate message detected: 12345
❌ Invalid webhook token from 192.168.1.1
```

### Métricas

**Endpoint**: `GET /metrics`

**Resposta**:
```json
{
  "status": "ok",
  "timestamp": "2025-10-16T10:30:00",
  "version": "1.0.0",
  "supervisor": {
    "total_conversations": 150,
    "intents": {
      "FAQ_ESTETICA": 45,
      "AGENDAR_AVALIACAO": 60,
      "LEAD_COMERCIAL": 30,
      "HUMANO": 15
    }
  },
  "circuit_breakers": {
    "guardrails": {
      "state": "closed",
      "failure_count": 0
    },
    "classifier": {
      "state": "closed",
      "failure_count": 0
    }
  }
}
```

---

## Troubleshooting

### Problema: Webhook não recebe mensagens

**Verificar**:
1. URL do webhook está correta no Chatwoot
2. Servidor está acessível publicamente (Railway)
3. Token está configurado corretamente
4. Evento `message_created` está selecionado

**Logs**:
```bash
# Verificar se webhook está chegando
tail -f logs/app.log | grep "Webhook received"
```

### Problema: Token inválido

**Verificar**:
1. `CHATWOOT_WEBHOOK_TOKEN` no `.env`
2. Header `api_access_token` no Chatwoot
3. Tokens são idênticos (sem espaços extras)

**Teste**:
```bash
curl -X POST http://localhost:8000/test/webhook \
  -H "api_access_token: $CHATWOOT_WEBHOOK_TOKEN"
```

### Problema: Mensagens duplicadas

**Verificar**:
1. `MESSAGE_DEDUP_TTL_SECONDS` está configurado
2. Chatwoot não está configurado com múltiplos webhooks
3. Logs mostram "Duplicate message detected"

**Solução**: Aumentar TTL se necessário
```bash
MESSAGE_DEDUP_TTL_SECONDS=600  # 10 minutos
```

### Problema: Resposta não chega no Chatwoot

**Verificar**:
1. `CHATWOOT_BASE_URL` e `CHATWOOT_TOKEN` corretos
2. `CHATWOOT_ACCOUNT_ID` correto
3. Logs mostram "Resposta enviada"

**Teste**:
```python
from app.tools.chatwoot import health_check
status = await health_check()
print(status)
```

### Problema: Message batching não funciona

**Verificar**:
1. `MESSAGE_PROCESSING_DELAY_SECONDS` > 0
2. Mensagens são do mesmo `conversation_id`
3. Mensagens chegam dentro do delay

**Desabilitar** (para debug):
```bash
MESSAGE_PROCESSING_DELAY_SECONDS=0
```

---

## Referências

### Documentação Oficial

- [Chatwoot Webhooks](https://www.chatwoot.com/docs/product/channels/api/webhooks)
- [Chatwoot API Reference](https://www.chatwoot.com/developers/api/)
- [Chatwoot Message Format](https://www.chatwoot.com/hc/user-guide/articles/1677693021)

### Arquivos do Projeto

- `app/tools/chatwoot.py` - Cliente API
- `server/main.py` - Webhook endpoint
- `app/config.py` - Configurações
- `tests/test_chatwoot_integration_complete.py` - Testes
- `.env.example` - Template de variáveis

### Endpoints Importantes

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/webhook/chatwoot` | POST | Recebe webhooks do Chatwoot |
| `/test/webhook` | POST | Testa autenticação do webhook |
| `/test/message` | POST | Testa processamento de mensagem |
| `/health` | GET | Health check do sistema |
| `/metrics` | GET | Métricas do sistema |
| `/api/conversations/{id}/return-to-ai` | POST | Retorna conversa para IA |

---

**Última Atualização**: 16 de Outubro de 2025  
**Versão do Sistema**: 1.0.0  
**Autor**: Sistema de Documentação Automática
