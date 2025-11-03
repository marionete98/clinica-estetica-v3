# 🚂 Variáveis de Ambiente para Railway
**Sistema:** Clínica Luana Multi-Agent  
**Ambiente:** Production

---

## 📋 Lista Completa de Variáveis

### ⚠️ OBRIGATÓRIAS (Sem essas o sistema NÃO inicia)

#### 🤖 LLM Configuration
```bash
MODEL_PROVIDER=xai
# Escolha: 'xai' ou 'gemini'

# Se escolher xAI Grok:
XAI_API_KEY=sk-your-xai-api-key-here
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1

# Se escolher Google Gemini:
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
```

#### 🗄️ Database (Supabase)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
```

#### 💾 Cache (Redis)
```bash
REDIS_URL=redis://default:password@your-redis-host:6379
```

#### 💬 Chatwoot Integration
```bash
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_API_TOKEN=your-chatwoot-api-token-here
CHATWOOT_WEBHOOK_TOKEN=your-webhook-secret-here
```

#### 📅 Calendar API
```bash
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
```

---

## ✅ RECOMENDADAS para Produção

#### 🔧 Application Settings
```bash
ENV=production
LOG_LEVEL=INFO
PORT=8000
```

#### 🤖 Agent Configuration
```bash
MAX_TOOL_CALLS_PER_SESSION=3
RESPONSE_TIMEOUT_SECONDS=10
MAX_CONTEXT_MESSAGES=20
```

#### 🚦 Rate Limiting
```bash
MAX_REQUESTS_PER_MINUTE=100
```

#### 📨 Message Processing
```bash
MESSAGE_DEDUP_TTL_SECONDS=300
MESSAGE_PROCESSING_DELAY_SECONDS=7
```

#### 🧠 FAQ Cache
```bash
FAQ_CACHE_ENABLED=true
FAQ_CACHE_TTL_SECONDS=3600
FAQ_CACHE_MAX_SIZE=100
```

#### ⏰ Business Hours
```bash
BUSINESS_HOURS_START=08:30
BUSINESS_HOURS_END=19:00
BUSINESS_HOURS_SAT_END=12:00
```

#### 📋 Policies
```bash
MIN_BOOKING_ADVANCE_HOURS=1
HARMONIZATION_CANCEL_HOURS=4
LASER_CANCEL_HOURS=24
MAX_RESCHEDULE_COUNT=2
```

#### 🔔 Reminders
```bash
REMINDER_D1_HOURS_BEFORE=24
REMINDER_H2_HOURS_BEFORE=2
```

---

## 📊 OPCIONAIS (Monitoramento)

#### 📈 Metrics Thresholds
```bash
P95_LATENCY_THRESHOLD_MS=7000
ERROR_RATE_THRESHOLD_PERCENT=2
HANDOVER_RATE_THRESHOLD_PERCENT=30
```

#### 🔔 Alerts
```bash
ALERT_EMAIL=admin@clinicaluana.com.br
ENABLE_EMAIL_ALERTS=false
```

#### 📡 Telemetry (OpenTelemetry)
```bash
ENABLE_TELEMETRY=true
TELEMETRY_SERVICE_NAME=clinica-luana-multi-agent
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4318
OTEL_EXPORTER_OTLP_INSECURE=true
```

---

## 🎯 Configuração Mínima Funcional

Se você está testando e quer o **mínimo para funcionar**, configure apenas:

```bash
# LLM (ESCOLHA UM)
MODEL_PROVIDER=xai
XAI_API_KEY=sk-your-key

# DATABASE
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key

# CACHE
REDIS_URL=redis://default:pass@host:6379

# CHATWOOT
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=123
CHATWOOT_API_TOKEN=your-token
CHATWOOT_WEBHOOK_TOKEN=your-secret

# CALENDAR
CALENDAR_API_URL=https://your-calendar-api.railway.app/api

# ENVIRONMENT
ENV=production
```

---

## 🚀 Configuração Completa Recomendada

Para **produção otimizada**, configure tudo:

```bash
# ============================================
# LLM Configuration
# ============================================
MODEL_PROVIDER=xai
XAI_API_KEY=sk-your-xai-api-key-here
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1

GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# ============================================
# Database (Supabase)
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# ============================================
# Cache (Redis)
# ============================================
REDIS_URL=redis://default:password@your-redis-host:6379
REDIS_PASSWORD=your-redis-password
REDIS_HOST=your-redis-host.cloud.redislabs.com
REDIS_PORT=6379

# ============================================
# Chatwoot
# ============================================
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_API_TOKEN=your-chatwoot-api-token-here
CHATWOOT_WEBHOOK_TOKEN=your-webhook-secret-here

# ============================================
# Calendar API
# ============================================
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
CALENDAR_API_TIMEOUT=10

# ============================================
# Application
# ============================================
ENV=production
LOG_LEVEL=INFO
PORT=8000

# ============================================
# Agent Configuration
# ============================================
MAX_TOOL_CALLS_PER_SESSION=3
RESPONSE_TIMEOUT_SECONDS=10
MAX_CONTEXT_MESSAGES=20

# ============================================
# Rate Limiting
# ============================================
MAX_REQUESTS_PER_MINUTE=100

# ============================================
# Message Processing
# ============================================
MESSAGE_DEDUP_TTL_SECONDS=300
MESSAGE_PROCESSING_DELAY_SECONDS=7

# ============================================
# FAQ Cache
# ============================================
FAQ_CACHE_ENABLED=true
FAQ_CACHE_TTL_SECONDS=3600
FAQ_CACHE_MAX_SIZE=100

# ============================================
# Business Hours
# ============================================
BUSINESS_HOURS_START=08:30
BUSINESS_HOURS_END=19:00
BUSINESS_HOURS_SAT_END=12:00

# ============================================
# Policies
# ============================================
MIN_BOOKING_ADVANCE_HOURS=1
HARMONIZATION_CANCEL_HOURS=4
LASER_CANCEL_HOURS=24
MAX_RESCHEDULE_COUNT=2

# ============================================
# Reminders
# ============================================
REMINDER_D1_HOURS_BEFORE=24
REMINDER_H2_HOURS_BEFORE=2

# ============================================
# Monitoring (Opcional)
# ============================================
P95_LATENCY_THRESHOLD_MS=7000
ERROR_RATE_THRESHOLD_PERCENT=2
HANDOVER_RATE_THRESHOLD_PERCENT=30

ALERT_EMAIL=admin@clinicaluana.com.br
ENABLE_EMAIL_ALERTS=false

# ============================================
# Telemetry (Opcional)
# ============================================
ENABLE_TELEMETRY=true
TELEMETRY_SERVICE_NAME=clinica-luana-multi-agent
```

---

## 📝 Como Adicionar no Railway

### Método 1: Interface Web
1. Acesse seu projeto no Railway
2. Vá em **Variables**
3. Clique em **+ New Variable**
4. Cole as variáveis uma por uma

### Método 2: Bulk Import (RECOMENDADO)
1. Acesse seu projeto no Railway
2. Vá em **Variables**
3. Clique em **Raw Editor**
4. Cole todas as variáveis de uma vez
5. Clique em **Save**

### Método 3: Railway CLI
```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Linkar projeto
railway link

# Adicionar variável
railway variables set MODEL_PROVIDER=xai

# Ou importar de arquivo
railway variables set -f .env.production
```

---

## ✅ Checklist de Validação

Após adicionar as variáveis, valide:

- [ ] **LLM Provider:** Escolheu `xai` ou `gemini`?
- [ ] **LLM API Key:** Adicionou a chave do provider escolhido?
- [ ] **Supabase:** URL e KEY corretos?
- [ ] **Redis:** URL de conexão funcional?
- [ ] **Chatwoot:** Account ID, token e webhook secret corretos?
- [ ] **Calendar API:** URL apontando para o serviço correto?
- [ ] **ENV:** Definido como `production`?
- [ ] **PORT:** Railway injeta automaticamente, mas pode deixar 8000

---

## 🔍 Como Obter as Credenciais

### xAI Grok
1. Acesse: https://console.x.ai/
2. Vá em **API Keys**
3. Gere uma nova chave
4. Copie e cole em `XAI_API_KEY`

### Google Gemini
1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API Key
3. Copie e cole em `GEMINI_API_KEY`

### Supabase
1. Acesse seu projeto no Supabase
2. **Settings** → **API**
3. Copie `URL` para `SUPABASE_URL`
4. Copie `service_role key` para `SUPABASE_KEY`

### Redis
1. Acesse seu Redis provider (Redis Cloud, Upstash, etc.)
2. Copie a connection string completa
3. Cole em `REDIS_URL`

### Chatwoot
1. Acesse seu Chatwoot
2. **Settings** → **Applications**
3. Crie um Access Token
4. Account ID está na URL: `app.chatwoot.com/app/accounts/{ID}`
5. Webhook secret: defina um valor forte e configure no webhook

### Calendar API
- Se você já tem o Calendar API rodando no Railway
- Use a URL pública do serviço

---

## 🚨 Segurança

### ⚠️ NUNCA commitar credenciais
- Todas essas variáveis devem estar **APENAS no Railway**
- Nunca adicionar ao `.env` versionado
- Usar `.env.local` para desenvolvimento local

### 🔐 Boas Práticas
- Use secrets fortes para `CHATWOOT_WEBHOOK_TOKEN`
- Rotacione API keys periodicamente
- Use service role key do Supabase (não anon key)
- Redis deve ter senha forte
- Habilite telemetria em produção para debugging

---

## 🎯 Ordem de Configuração Sugerida

1. ✅ **Primeiro:** ENV, MODEL_PROVIDER, chaves LLM
2. ✅ **Segundo:** Supabase, Redis, Chatwoot (infraestrutura)
3. ✅ **Terceiro:** Calendar API
4. ✅ **Quarto:** Configurações de negócio (horários, políticas)
5. ✅ **Último:** Monitoramento e telemetria (opcional)

---

## 🧪 Teste Após Configuração

Depois de adicionar todas as variáveis:

```bash
# 1. Faça deploy
git push railway main

# 2. Verifique logs
railway logs

# 3. Teste health check
curl https://your-app.railway.app/health

# 4. Teste webhook
# Configure o webhook no Chatwoot apontando para:
# https://your-app.railway.app/webhook/
```

---

## 📞 Suporte

Se tiver problemas:
1. Verifique os logs do Railway
2. Confirme que todas as variáveis obrigatórias foram definidas
3. Teste conexões individualmente (Supabase, Redis, Chatwoot)
4. Valide que o Calendar API está acessível

---

**Resumo:** Total de **48 variáveis** disponíveis  
- **13 obrigatórias** para funcionamento básico  
- **19 recomendadas** para produção otimizada  
- **16 opcionais** para monitoramento avançado
