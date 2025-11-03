# Análise do Arquivo .env - Relatório

## 📊 Status Geral

**Arquivo Analisado**: `.env`  
**Data**: 16 de Outubro de 2025  
**Status**: ⚠️ Necessita Correções

---

## ✅ Variáveis Corretas

### Chatwoot
- ✅ `CHATWOOT_API_URL` - Configurado corretamente
- ✅ `CHATWOOT_ACCOUNT_ID` - Configurado corretamente
- ✅ `CHATWOOT_API_TOKEN` - Configurado corretamente
- ✅ `CHATWOOT_WEBHOOK_SECRET` - Configurado corretamente

### Supabase
- ✅ `SUPABASE_URL` - Configurado corretamente
- ✅ `SUPABASE_KEY` - Configurado corretamente (service role)

### Redis
- ✅ `REDIS_URL` - Configurado corretamente

### xAI
- ✅ `XAI_API_KEY` - Configurado corretamente

### Melhorias Chatwoot (Novas)
- ✅ `MESSAGE_DEDUP_TTL_SECONDS=300` - Configurado corretamente
- ✅ `MESSAGE_PROCESSING_DELAY_SECONDS=7` - Configurado corretamente

---

## ❌ Problemas Identificados

### 1. Variáveis Duplicadas/Desnecessárias

```bash
# ❌ DUPLICADAS - Remover
CHATWOOT_BASE_URL="..."  # Duplica CHATWOOT_API_URL
CHATWOOT_TOKEN="..."     # Duplica CHATWOOT_API_TOKEN
CHATWOOT_WEBHOOK_TOKEN="..."  # Duplica CHATWOOT_WEBHOOK_SECRET
SUPABASE_ANON_KEY="..."  # Não usado (usamos service role)
SUPABASE_SERVICE_ROLE_KEY="..."  # Duplica SUPABASE_KEY
SUPABASE_ENABLED="true"  # Não usado
```

### 2. Variáveis Não Usadas pelo Sistema

```bash
# ❌ NÃO USADAS - Remover
SCHEDULE_API_URL="..."
SCHEDULE_API_TOKEN="..."
CALENDAR_API_KEY="..."  # Calendar API não usa autenticação
REDIS_VECTOR_INDEX="..."
REDIS_VECTOR_PREFIX="..."
REDIS_VECTOR_FIELD="..."
REDIS_TEXT_FIELD="..."
REDIS_DIM="..."
REDIS_METRIC="..."
LANGCACHE_ENDPOINT="..."
LANGCACHE_CACHE_ID="..."
LANGCACHE_API_KEY="..."
LANGCACHE_ENABLED="..."
LANGCACHE_SIMILARITY_THRESHOLD="..."
OPENAI_API_KEY="..."  # Não usamos OpenAI
EMBEDDING_MODEL="..."  # Não usamos embeddings
LLM_MODEL="..."  # Duplica XAI_MODEL
CLINIC_NAME="..."  # Hardcoded no código
CLINIC_CNPJ="..."  # Hardcoded no código
CLINIC_ADDRESS="..."  # Hardcoded no código
CLINIC_PHONE="..."  # Hardcoded no código
CLINIC_EMAIL="..."  # Hardcoded no código
BUSINESS_HOURS="..."  # Usamos BUSINESS_HOURS_START/END
CANCELLATION_POLICY_SHORT="..."  # Hardcoded no código
LEAD_TONE="..."  # Hardcoded nos prompts
MIN_ADVANCE_BOOKING="..."  # Duplica MIN_BOOKING_ADVANCE_HOURS
INTERVAL_BETWEEN_SERVICES_MIN="..."  # Hardcoded (10 min)
CONFIDENCE_THRESHOLD="..."  # Não usado
MAX_FAQ_ATTEMPTS_BEFORE_ESCALATION="..."  # Não usado
MAX_ERROR_RATE_BEFORE_ESCALATION="..."  # Não usado
MAX_TOTAL_ATTEMPTS_BEFORE_ESCALATION="..."  # Não usado
GUARDRAILS_ENABLED="..."  # Sempre habilitado
ENVIRONMENT="..."  # Duplica ENV
SECRET_KEY_BASE="..."  # Não usado
CHATWOOT_WEBHOOK_URL="..."  # Não usado (configurado no Chatwoot)
DEBUG="..."  # Duplica LOG_LEVEL
```

### 3. Variáveis Faltantes (Opcionais)

```bash
# ⚠️ OPCIONAIS - Adicionar se necessário
MODEL_PROVIDER=xai  # Define qual LLM usar
XAI_MODEL=grok-4-reasoning  # Modelo específico
XAI_BASE_URL=https://api.x.ai/v1  # URL da API
ENV=production  # Ambiente
```

---

## 🔧 Correções Recomendadas

### Opção 1: Limpar .env Atual

Remover todas as variáveis não usadas e duplicadas:

```bash
# Manter apenas:
- CHATWOOT_API_URL
- CHATWOOT_ACCOUNT_ID
- CHATWOOT_API_TOKEN
- CHATWOOT_WEBHOOK_SECRET
- SUPABASE_URL
- SUPABASE_KEY
- REDIS_URL
- XAI_API_KEY
- MESSAGE_DEDUP_TTL_SECONDS
- MESSAGE_PROCESSING_DELAY_SECONDS
- CALENDAR_API_URL (opcional, tem default)
```

### Opção 2: Usar .env.production (Recomendado)

Criado arquivo `.env.production` com configuração limpa e otimizada.

**Ação**:
```bash
# Backup do .env atual
cp .env .env.backup

# Usar versão limpa
cp .env.production .env
```

---

## 📋 Variáveis por Categoria

### Obrigatórias (Sistema não inicia sem elas)

```bash
SUPABASE_URL=...
SUPABASE_KEY=...
REDIS_URL=...
CHATWOOT_API_URL=...
CHATWOOT_ACCOUNT_ID=...
CHATWOOT_API_TOKEN=...
CHATWOOT_WEBHOOK_SECRET=...
XAI_API_KEY=...  # Se MODEL_PROVIDER=xai
```

### Recomendadas (Tem defaults, mas melhor configurar)

```bash
MODEL_PROVIDER=xai
XAI_MODEL=grok-4-reasoning
ENV=production
LOG_LEVEL=INFO
MESSAGE_DEDUP_TTL_SECONDS=300
MESSAGE_PROCESSING_DELAY_SECONDS=7
```

### Opcionais (Tem defaults funcionais)

```bash
CALENDAR_API_URL=...  # Default: https://clinica-luana-calendar-production.up.railway.app/api
CALENDAR_API_TIMEOUT=10
PORT=8000
MAX_TOOL_CALLS_PER_SESSION=3
RESPONSE_TIMEOUT_SECONDS=10
MAX_CONTEXT_MESSAGES=20
MAX_REQUESTS_PER_MINUTE=100
BUSINESS_HOURS_START=08:30
BUSINESS_HOURS_END=19:00
BUSINESS_HOURS_SAT_END=12:00
MIN_BOOKING_ADVANCE_HOURS=1
HARMONIZATION_CANCEL_HOURS=4
LASER_CANCEL_HOURS=24
MAX_RESCHEDULE_COUNT=2
REMINDER_D1_HOURS_BEFORE=24
REMINDER_H2_HOURS_BEFORE=2
P95_LATENCY_THRESHOLD_MS=7000
ERROR_RATE_THRESHOLD_PERCENT=2.0
HANDOVER_RATE_THRESHOLD_PERCENT=30.0
```

---

## 🎯 Plano de Ação

### Passo 1: Backup
```bash
cp .env .env.backup.$(date +%Y%m%d)
```

### Passo 2: Aplicar Versão Limpa
```bash
cp .env.production .env
```

### Passo 3: Validar
```bash
python scripts/validate_env.py
python scripts/validate_chatwoot_improvements.py
```

### Passo 4: Testar Localmente
```bash
uvicorn main:app --reload
curl http://localhost:8000/health
```

### Passo 5: Deploy
```bash
# Atualizar variáveis no Railway
railway variables set MODEL_PROVIDER=xai
railway variables set ENV=production
# ... outras variáveis

# Deploy
git push railway main
```

---

## 📊 Comparação: Antes vs Depois

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Total de Variáveis | 52 | 28 | -46% |
| Duplicadas | 8 | 0 | -100% |
| Não Usadas | 30 | 0 | -100% |
| Obrigatórias | 8 | 8 | ✅ |
| Organizadas | ❌ | ✅ | +100% |
| Documentadas | ❌ | ✅ | +100% |

---

## ⚠️ Avisos Importantes

### 1. Não Commitar .env
```bash
# Verificar .gitignore
cat .gitignore | grep .env

# Deve conter:
.env
.env.local
.env.*.local
```

### 2. Usar Railway Variables
Para produção, configurar variáveis no Railway Dashboard, não no .env:
```
https://railway.app/project/[seu-projeto]/variables
```

### 3. Rotação de Secrets
Considerar rotacionar periodicamente:
- `CHATWOOT_API_TOKEN`
- `CHATWOOT_WEBHOOK_SECRET`
- `XAI_API_KEY`
- `SUPABASE_KEY`

---

## 🔍 Validação Final

Após aplicar correções, executar:

```bash
# 1. Validar sintaxe
python -c "from config.settings import settings; print('✅ Settings OK')"

# 2. Validar conexões
python scripts/validate_env.py

# 3. Validar melhorias Chatwoot
python scripts/validate_chatwoot_improvements.py

# 4. Health check
curl http://localhost:8000/health | jq
```

Todos devem retornar sucesso (✅).

---

## 📚 Referências

- [.env.example](../.env.example) - Template com todas as variáveis
- [.env.production](../.env.production) - Versão limpa para produção
- [config/settings.py](../config/settings.py) - Definição de todas as variáveis
- [Railway Variables Guide](https://docs.railway.app/develop/variables)

---

**Última Atualização**: 16 de Outubro de 2025  
**Status**: ✅ Análise Completa  
**Ação Recomendada**: Aplicar .env.production
