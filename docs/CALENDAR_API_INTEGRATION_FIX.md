# 🔧 Correção da Integração Calendar API

## ❌ **PROBLEMA CRÍTICO IDENTIFICADO**

O sistema multi-agente **NÃO está usando o Calendar API corretamente**!

### Incompatibilidades Encontradas:

1. **Tabelas Diferentes**:
   - Calendar API: `appointments` (Next.js)
   - Sistema Python: `services` (busca direta no Supabase)

2. **Estrutura de Dados Incompatível**:
   - Calendar API usa: `procedure`, `treatment`, `duration` (string)
   - Sistema Python espera: `name`, `category`, `duration_min` (int)

3. **Endpoints Não Utilizados**:
   - `calendar_api_client.py` implementa corretamente os endpoints
   - `scheduler_tools.py` **ignora** o client e busca direto no Supabase

---

## ✅ **SOLUÇÃO: Refatorar scheduler_tools.py**

### **Mudanças Necessárias:**

#### 1. **Remover busca direta em `services`**
```python
# ❌ ERRADO (atual):
service = await get_service_by_id(UUID(service_id))
# Busca em: supabase.table("services")

# ✅ CORRETO (novo):
# Buscar procedimentos via Calendar API
procedures = await calendar_client.get_procedures()
# Ou criar endpoint /procedures no Calendar API
```

#### 2. **Usar `appointments` ao invés de `services`**
```python
# ❌ ERRADO:
async def list_available_slots(service_id: str, ...):
    service = await get_service_by_id(UUID(service_id))
    # ...

# ✅ CORRETO:
async def list_available_slots(procedure_name: str, ...):
    # Buscar appointments existentes via Calendar API
    existing = await calendar_client.get_appointments(
        start_date=start_date,
        end_date=end_date
    )
    # Filtrar por procedure_name
    # ...
```

#### 3. **Mapear campos corretamente**
```python
# Mapeamento Calendar API → Sistema Python
appointment_data = {
    "client_name": contact.name,
    "client_phone": contact.phone,
    "client_email": contact.email,
    "appointment_date": start_dt.date().isoformat(),
    "start_time": start_dt.time().strftime('%H:%M'),
    "end_time": end_dt.time().strftime('%H:%M'),
    "duration": f"{duration_min}min",
    "procedure": service_name,  # ← Não "name"
    "treatment": category,      # ← Não "category"
    "room": room_name,          # ← String, não UUID
    "observations": f"Agendado via WhatsApp",
    "status": "scheduled"
}
```

---

## 🔄 **ARQUITETURA CORRETA**

```
┌─────────────────────────────────────────────────────────────┐
│ Sistema Multi-Agente (Python)                               │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ scheduler_tools.py                               │      │
│  │                                                  │      │
│  │  list_available_slots()                         │      │
│  │  create_booking()                               │      │
│  │  get_patient_bookings()                         │      │
│  │                                                  │      │
│  │  ↓ USA                                          │      │
│  │                                                  │      │
│  │  calendar_api_client.py                         │      │
│  │  ├─ get_appointments()                          │      │
│  │  ├─ create_appointment()                        │      │
│  │  ├─ update_appointment()                        │      │
│  │  └─ delete_appointment()                        │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Calendar API (Next.js)                                      │
│ https://clinica-luana-calendar-production.up.railway.app    │
│                                                             │
│  /api/appointments                                          │
│  ├─ GET    (list/filter)                                   │
│  ├─ POST   (create)                                        │
│  ├─ PUT    (update)                                        │
│  └─ DELETE (soft delete)                                   │
│                                                             │
│  ↓ Acessa                                                  │
│                                                             │
│  Supabase: table("appointments")                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 **CHECKLIST DE CORREÇÃO**

### ✅ **Fase 1: Validação**
- [ ] Confirmar que Calendar API está no ar
- [ ] Testar endpoints manualmente
- [ ] Verificar estrutura da tabela `appointments`
- [ ] Documentar campos obrigatórios

### ✅ **Fase 2: Refatoração**
- [ ] Remover dependência de `table("services")`
- [ ] Atualizar `scheduler_tools.py` para usar `calendar_api_client`
- [ ] Mapear campos corretamente (procedure, treatment, etc.)
- [ ] Atualizar testes

### ✅ **Fase 3: Migração de Dados**
- [ ] Criar endpoint `/procedures` no Calendar API (se necessário)
- [ ] Migrar dados de `services` → `appointments` (se houver)
- [ ] Atualizar seed scripts

### ✅ **Fase 4: Testes**
- [ ] Testar `list_available_slots` com Calendar API
- [ ] Testar `create_booking` com Calendar API
- [ ] Testar `get_patient_bookings` com Calendar API
- [ ] Validar end-to-end

---

## 🚨 **IMPACTO**

**Crítico**: Sistema atual **NÃO funciona** corretamente porque:
1. Busca dados em tabela errada (`services` vs `appointments`)
2. Não usa o Calendar API implementado
3. Dados não sincronizados entre sistemas

**Prioridade**: **ALTA** - Corrigir antes do deploy

---

## 📚 **Referências**

- Calendar API Docs: `docs/CALENDAR_API_DOCS.md`
- Calendar API Source: `clinica-luana-calendar/app/api/appointments/route.ts`
- Client Implementation: `tools/calendar_api_client.py`
- Scheduler Tools: `tools/scheduler_tools.py`

---

**Data**: 2025-10-20
**Status**: ❌ **CRÍTICO - REQUER CORREÇÃO IMEDIATA**
