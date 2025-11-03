# 🗄️ Migrações de Banco de Dados Aplicadas

**Data:** 2025-10-17  
**Projeto:** Clínica Luana Multi-Agent System  
**Supabase Project:** pbngysiofdeqpmxbcxzd

---

## 📋 Resumo das Migrações

Foram aplicadas **6 migrações** para alinhar o schema do Supabase com o código da aplicação:

1. ✅ Colunas timestamp em `appointments`
2. ✅ Tabela `logs` para observabilidade
3. ✅ Tabela `message_templates` com templates padrão
4. ✅ Tabela `contacts` (migração de `clients`)
5. ✅ Foreign keys em `appointments`
6. ✅ Tabela `sessions` para gestão de contexto

---

## 🔧 Detalhamento das Correções

### 1️⃣ **Migração: `add_appointments_timestamp_columns`**

**Problema:** Código esperava `start_ts` e `end_ts` (TIMESTAMPTZ), mas o banco tinha `appointment_date` + `appointment_time` separados.

**Solução:**
```sql
ALTER TABLE appointments ADD COLUMN:
- start_ts TIMESTAMPTZ (populado de appointment_date + start_time)
- end_ts TIMESTAMPTZ (populado de appointment_date + end_time)
- reminder_d1_sent BOOLEAN DEFAULT FALSE
- reminder_h2_sent BOOLEAN DEFAULT FALSE
- feedback_sent BOOLEAN DEFAULT FALSE
```

**Resultado:**
- ✅ 7 appointments com `start_ts` e `end_ts` populados
- ✅ Flags de reminder prontos para jobs de agendamento

---

### 2️⃣ **Migração: `create_logs_table`**

**Problema:** Métricas e alertas falhavam com erro `table 'public.logs' not found`.

**Solução:**
```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    conversation_id TEXT,
    contact_id UUID,
    intent TEXT,
    provider TEXT CHECK (provider IN ('xai', 'gemini')),
    latency_ms INTEGER CHECK (latency_ms >= 0),
    tools_used TEXT[],
    cost_estimate DECIMAL(10, 6),
    error_message TEXT,
    request_payload JSONB,
    response_payload JSONB
);

-- Índices para queries de métricas
CREATE INDEX idx_logs_ts ON logs(ts DESC);
CREATE INDEX idx_logs_conversation_id ON logs(conversation_id);
CREATE INDEX idx_logs_intent ON logs(intent);
CREATE INDEX idx_logs_error ON logs(error_message) WHERE error_message IS NOT NULL;
```

**Resultado:**
- ✅ Tabela criada e pronta para receber logs
- ✅ Jobs de alertas (`services/alerts.py`) e métricas (`services/metrics.py`) funcionarão

---

### 3️⃣ **Migração: `create_message_templates_table`**

**Problema:** Cache de templates falhava com erro `table 'public.message_templates' not found`.

**Solução:**
```sql
CREATE TABLE message_templates (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    variables TEXT[],
    category TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Templates padrão inseridos
INSERT INTO message_templates VALUES
- D1_REMINDER (lembrete 1 dia antes)
- H2_REMINDER (lembrete 2 horas antes)
- FEEDBACK_REQUEST (solicitação de feedback pós-tratamento)
```

**Resultado:**
- ✅ 3 templates padrão criados
- ✅ Cache de KB (`services/kb_cache_service.py`) sincroniza templates com sucesso

---

### 4️⃣ **Migração: `create_contacts_table`**

**Problema:** Código esperava tabela `contacts`, mas banco tinha apenas `clients`.

**Solução:**
```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    phone TEXT NOT NULL UNIQUE,
    name TEXT,
    email TEXT,
    consent BOOLEAN DEFAULT FALSE,
    no_show_count INTEGER DEFAULT 0
);

-- Migração de dados existentes
INSERT INTO contacts (phone, name, email, ...)
SELECT phone, name, email, ... FROM clients
WHERE phone IS NOT NULL;
```

**Resultado:**
- ✅ 4 registros migrados de `clients` para `contacts`
- ✅ Health checks (`main.py`, `routes/api.py`) funcionam sem erros 404

---

### 5️⃣ **Migração: `add_appointments_foreign_keys`**

**Problema:** Modelo `Appointment` esperava FKs (`contact_id`, `service_id`, `room_id`), mas banco tinha apenas campos de texto.

**Solução:**
```sql
ALTER TABLE appointments ADD COLUMN:
- contact_id UUID REFERENCES clients(id)
- service_id UUID REFERENCES procedures(id)
- room_id UUID REFERENCES rooms(id)
- equipment_id UUID
- reschedule_count INTEGER DEFAULT 0 CHECK (reschedule_count BETWEEN 0 AND 2)
- cancellation_reason TEXT

-- População automática (best-effort)
UPDATE appointments SET contact_id = (SELECT id FROM clients WHERE phone = client_phone);
UPDATE appointments SET service_id = (SELECT id FROM procedures WHERE name = procedure_name);
UPDATE appointments SET room_id = (SELECT id FROM rooms WHERE name = room);
```

**Resultado:**
- ✅ 4/7 appointments com `contact_id` populado
- ✅ 4/7 appointments com `service_id` populado
- ✅ 4/7 appointments com `room_id` populado
- ⚠️ 3 appointments sem FKs (procedure_name era NULL)

---

### 6️⃣ **Migração: `create_sessions_table`**

**Problema:** Código referenciava tabela `sessions` para backup de contexto Redis.

**Solução:**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    conversation_id TEXT NOT NULL UNIQUE,
    contact_id UUID REFERENCES clients(id),
    summary TEXT,
    last_intent TEXT,
    automation_paused BOOLEAN DEFAULT FALSE,
    human_takeover_reason TEXT
);

CREATE INDEX idx_sessions_conversation_id ON sessions(conversation_id);
CREATE INDEX idx_sessions_automation_paused ON sessions(automation_paused);
```

**Resultado:**
- ✅ Tabela criada e pronta para armazenar sessões
- ✅ Backup de contexto além do Redis (TTL 7 dias)

---

## 📊 Estado Final do Banco

| Tabela | Registros | Colunas Principais | Status |
|--------|-----------|-------------------|--------|
| `appointments` | 7 | id, contact_id, service_id, start_ts, end_ts, reminder_d1_sent, reminder_h2_sent | ✅ Completa |
| `clients` | 4 | id, name, phone, email | ✅ Existente |
| `contacts` | 4 | id, phone, name, email, consent | ✅ Nova (migrada) |
| `procedures` | 26 | id, name, category, duration_minutes | ✅ Existente |
| `rooms` | 10 | id, name, description | ✅ Existente |
| `logs` | 0 | id, ts, conversation_id, intent, latency_ms, error_message | ✅ Nova (vazia) |
| `message_templates` | 3 | id, name, content, variables | ✅ Nova (3 templates) |
| `sessions` | 0 | id, conversation_id, contact_id, automation_paused | ✅ Nova (vazia) |
| `knowledge_base` | 79 | id, title, content, category | ✅ Existente |

---

## 🚨 Avisos e Próximos Passos

### ⚠️ **Appointments Sem FKs**
3 appointments não têm `contact_id` ou `service_id` porque `procedure_name` era NULL. Opções:
1. Popular manualmente via SQL UPDATE
2. Deletar esses appointments (se forem dados de teste)
3. Deixar NULL e o código lida com isso

### ⚠️ **Dados Legados**
As colunas antigas (`client_name`, `client_phone`, `procedure_name`, `appointment_date`, `appointment_time`) ainda existem. Opções:
1. Manter para compatibilidade retroativa
2. Deprecar gradualmente após migração completa
3. Remover em migração futura (não recomendado imediatamente)

### ✅ **Logs Operacionais**
A tabela `logs` está vazia. Ela será populada quando:
- Webhooks do Chatwoot receberem mensagens
- Agente orquestrador processar interações
- Sistema calcular métricas (latência, handover rate, etc.)

### ✅ **RLS Habilitado**
Todas as novas tabelas têm Row Level Security (RLS) habilitado com políticas para `service_role`:
- `logs` → service_role tem acesso total
- `message_templates` → service_role tem acesso total
- `contacts` → service_role tem acesso total
- `sessions` → service_role tem acesso total

---

## 🔍 Verificação

Para confirmar que tudo está correto, execute:

```sql
-- Verificar estrutura de appointments
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'appointments' 
  AND column_name IN ('start_ts', 'end_ts', 'contact_id', 'service_id', 
                       'reminder_d1_sent', 'reminder_h2_sent');

-- Verificar tabelas criadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('logs', 'message_templates', 'contacts', 'sessions');

-- Verificar templates padrão
SELECT name, category, active FROM message_templates;

-- Verificar appointments populados
SELECT COUNT(*) as total,
       COUNT(contact_id) as with_contact,
       COUNT(service_id) as with_service,
       COUNT(start_ts) as with_timestamp
FROM appointments;
```

---

## 📝 Changelog

- **2025-10-17**: Migrações iniciais aplicadas
  - Criadas 4 novas tabelas (`logs`, `message_templates`, `contacts`, `sessions`)
  - Adicionadas 9 novas colunas em `appointments`
  - Migrados 4 registros de `clients` para `contacts`
  - Populados 7 timestamps em `appointments`
  - Criados 3 templates padrão

---

## 🎯 Erros Corrigidos

| Erro Log | Status |
|----------|--------|
| `Could not find the table 'public.contacts'` | ✅ Resolvido |
| `Could not find the table 'public.logs'` | ✅ Resolvido |
| `Could not find the table 'public.message_templates'` | ✅ Resolvido |
| `column appointments.start_ts does not exist` | ✅ Resolvido |
| `column appointments.reminder_d1_sent does not exist` | ✅ Resolvido |
| `column appointments.reminder_h2_sent does not exist` | ✅ Resolvido |

---

**Próximo Deploy:** Todos os erros de schema devem desaparecer. O sistema estará pronto para operar com logs, métricas, alertas e reminders funcionais! 🚀
