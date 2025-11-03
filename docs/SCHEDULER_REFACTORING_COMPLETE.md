# ✅ Refatoração do Scheduler - CONCLUÍDA

**Data**: 2025-10-20  
**Status**: ✅ **COMPLETO**  
**Prioridade**: 🔴 **CRÍTICA**

---

## 🎯 **Objetivo**

Refatorar `tools/scheduler_tools.py` para usar **Calendar API corretamente**, eliminando dependência da tabela `services` e alinhando com a arquitetura do sistema de agendamento Next.js.

---

## ✅ **Mudanças Implementadas**

### 1️⃣ **`list_available_slots()` - REFATORADO**

#### **Antes:**
```python
async def list_available_slots(
    service_id: str,  # ❌ UUID da tabela services
    date_range: int = 7,
    start_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    # Buscava direto no Supabase
    service = await get_service_by_id(UUID(service_id))
    # ...
```

#### **Depois:**
```python
async def list_available_slots(
    procedure_name: str,  # ✅ Nome do procedimento
    duration_min: int = 60,  # ✅ Duração em minutos
    date_range: int = 7,
    start_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    # Usa Calendar API
    calendar_client = await get_calendar_client()
    existing_appointments = await calendar_client.get_appointments(...)
    # ...
```

#### **Benefícios:**
- ✅ Usa Calendar API como fonte de verdade
- ✅ Não depende mais de `table("services")`
- ✅ Parâmetros mais simples e diretos
- ✅ Compatível com estrutura do Calendar API

---

### 2️⃣ **`create_booking()` - REFATORADO**

#### **Antes:**
```python
async def create_booking(
    contact_id: str,
    service_id: str,  # ❌ UUID da tabela services
    start_datetime: str,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    # Buscava service e room no Supabase
    service = await get_service_by_id(UUID(service_id))
    room_data = await supabase_ops.aselect(table='rooms', ...)
    # ...
```

#### **Depois:**
```python
async def create_booking(
    contact_id: str,
    procedure_name: str,  # ✅ Nome do procedimento
    treatment_category: str,  # ✅ Categoria do tratamento
    duration_min: int,  # ✅ Duração
    start_datetime: str,
    room: Optional[str] = None,  # ✅ Nome da sala (string)
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    # Cria direto via Calendar API
    appointment_data = {
        "procedure": procedure_name,
        "treatment": treatment_category,
        "duration": f"{duration_min}min",
        "room": room or "A definir",
        # ...
    }
    calendar_appointment = await calendar_client.create_appointment(appointment_data)
    # ...
```

#### **Benefícios:**
- ✅ Mapeamento correto de campos (procedure, treatment)
- ✅ Usa Calendar API para criação
- ✅ Não depende de `table("services")` ou `table("rooms")`
- ✅ Tracking interno opcional (não bloqueia se falhar)

---

### 3️⃣ **Metadata de Tools - ATUALIZADO**

#### **Antes:**
```python
SCHEDULER_TOOLS = {
    "list_available_slots": {
        "parameters": {
            "properties": {
                "service_id": {"type": "string"},  # ❌
                # ...
            },
            "required": ["service_id"]
        }
    },
    "create_booking": {
        "parameters": {
            "properties": {
                "service_id": {"type": "string"},  # ❌
                # ...
            },
            "required": ["contact_id", "service_id", "start_datetime"]
        }
    }
}
```

#### **Depois:**
```python
SCHEDULER_TOOLS = {
    "list_available_slots": {
        "parameters": {
            "properties": {
                "procedure_name": {"type": "string"},  # ✅
                "duration_min": {"type": "integer", "default": 60},  # ✅
                # ...
            },
            "required": ["procedure_name"]
        }
    },
    "create_booking": {
        "parameters": {
            "properties": {
                "procedure_name": {"type": "string"},  # ✅
                "treatment_category": {"type": "string"},  # ✅
                "duration_min": {"type": "integer"},  # ✅
                "room": {"type": "string"},  # ✅ Opcional
                # ...
            },
            "required": ["contact_id", "procedure_name", "treatment_category", "duration_min", "start_datetime"]
        }
    }
}
```

---

### 4️⃣ **Imports - LIMPO**

#### **Removido:**
```python
from models.repository import (
    get_service_by_id,  # ❌ Removido
    get_contact_by_id,
    create_appointment as repo_create_appointment
)
```

#### **Mantido:**
```python
from models.repository import (
    get_contact_by_id,  # ✅ Ainda necessário
    create_appointment as repo_create_appointment  # ✅ Tracking opcional
)
```

---

## 📊 **Comparação de Estrutura**

### **Dados Enviados ao Calendar API**

| Campo | Antes (Errado) | Depois (Correto) |
|-------|----------------|------------------|
| Procedimento | `service.name` | `procedure_name` ✅ |
| Categoria | `service.category` | `treatment_category` ✅ |
| Duração | `service.duration_min` (int) | `f"{duration_min}min"` (string) ✅ |
| Sala | `room_id` (UUID) | `room` (string) ✅ |
| Status | `"confirmed"` | `"scheduled"` ✅ |

---

## 🎯 **Arquitetura Corrigida**

```
┌─────────────────────────────────────────────────────────────┐
│ Sistema Multi-Agente (Python)                               │
│                                                             │
│  scheduler_tools.py                                         │
│  ├─ list_available_slots(procedure_name, duration_min)     │
│  ├─ create_booking(procedure_name, treatment_category, ...) │
│  └─ get_patient_bookings(phone)                            │
│                                                             │
│  ↓ USA (via calendar_api_client.py)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Calendar API (Next.js)                                      │
│ https://clinica-luana-calendar-production.up.railway.app    │
│                                                             │
│  /api/appointments                                          │
│  ├─ GET    (list/filter) ✅                                │
│  ├─ POST   (create) ✅                                     │
│  ├─ PUT    (update) ✅                                     │
│  └─ DELETE (soft delete) ✅                                │
│                                                             │
│  ↓ Acessa                                                  │
│  Supabase: table("appointments") ✅                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ **Checklist de Validação**

### **Código**
- [x] Remover dependência de `get_service_by_id()`
- [x] Atualizar `list_available_slots()` para usar `procedure_name`
- [x] Atualizar `create_booking()` para mapear campos corretamente
- [x] Atualizar metadata de tools (SCHEDULER_TOOLS)
- [x] Remover imports não utilizados
- [x] Corrigir logs que referenciam `service_id`

### **Compatibilidade**
- [x] Campos mapeados corretamente (procedure, treatment, duration)
- [x] Status correto ("scheduled" vs "confirmed")
- [x] Room como string (não UUID)
- [x] Usa Calendar API como fonte de verdade

### **Documentação**
- [x] Criar `CALENDAR_API_INTEGRATION_FIX.md`
- [x] Criar `SCHEDULER_REFACTORING_COMPLETE.md`
- [x] Atualizar docstrings das funções

---

## 🧪 **Próximos Passos**

### 1️⃣ **Testes** (PENDENTE)
```bash
# Criar teste de integração
python test_scheduler_refactored.py
```

### 2️⃣ **Validação End-to-End** (PENDENTE)
- [ ] Testar `list_available_slots` com Calendar API real
- [ ] Testar `create_booking` com Calendar API real
- [ ] Verificar dados no Supabase (table appointments)
- [ ] Validar fluxo completo via WhatsApp

### 3️⃣ **Atualizar Agentes** (PENDENTE)
- [ ] Atualizar `agents/scheduler.py` para usar novos parâmetros
- [ ] Atualizar prompts do Scheduler Agent
- [ ] Testar fluxo de agendamento completo

---

## 📚 **Referências**

- **Calendar API Docs**: `docs/CALENDAR_API_DOCS.md`
- **Calendar API Source**: `clinica-luana-calendar/app/api/appointments/route.ts`
- **Client Implementation**: `tools/calendar_api_client.py`
- **Scheduler Tools (Refatorado)**: `tools/scheduler_tools.py`
- **Problema Original**: `docs/CALENDAR_API_INTEGRATION_FIX.md`

---

## 🎉 **Resultado**

### **Antes:**
❌ Sistema buscava em `table("services")` que não existe no Calendar API  
❌ Dados não sincronizados entre sistemas  
❌ Campos incompatíveis (name vs procedure, category vs treatment)  
❌ Calendar API implementado mas **NÃO USADO**

### **Depois:**
✅ Sistema usa Calendar API como fonte de verdade  
✅ Dados sincronizados via API REST  
✅ Campos mapeados corretamente  
✅ Arquitetura alinhada com Next.js Calendar  

---

**Status**: ✅ **REFATORAÇÃO COMPLETA**  
**Próximo**: 🧪 **TESTES E VALIDAÇÃO**
