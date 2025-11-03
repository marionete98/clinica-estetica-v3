# 📅 Calendar API Documentation

**Base URL**: `https://clinica-luana-calendar-production.up.railway.app/api`

---

## 🔗 Endpoints

### 1. **GET /appointments**
Lista agendamentos com filtros opcionais.

**Query Parameters**:
- `date` (string): Filtrar por data específica (YYYY-MM-DD)
- `start_date` (string): Data inicial do range (YYYY-MM-DD)
- `end_date` (string): Data final do range (YYYY-MM-DD)
- `bypass_cache` (boolean): Bypass do cache Redis

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "client_name": "Maria Silva",
      "client_phone": "+5511999999999",
      "client_email": "maria@email.com",
      "appointment_date": "2025-10-20",
      "start_time": "09:00",
      "end_time": "10:00",
      "duration": "1h",
      "procedure": "Ácido Hialurônico",
      "treatment": "Harmonização facial",
      "room": "Sala 01",
      "observations": "Primeira consulta",
      "status": "scheduled",
      "whatsapp_sent": false,
      "reminder_sent": false,
      "color": "bg-[#ff9999]",
      "service_id": "uuid",
      "contact_id": "uuid",
      "room_id": "uuid"
    }
  ],
  "count": 1,
  "mode": "database",
  "cached": false
}
```

---

### 2. **POST /appointments**
Cria um novo agendamento.

**Required Fields**:
- `client_name` (string): Nome do cliente
- `appointment_date` (string): Data do agendamento (YYYY-MM-DD)
- `start_time` (string): Hora de início (HH:MM)
- `end_time` (string): Hora de término (HH:MM)
- `procedure` (string): Nome do procedimento
- `treatment` (string): Nome do tratamento

**Optional Fields**:
- `client_phone` (string): Telefone do cliente
- `client_email` (string): Email do cliente
- `duration` (string): Duração formatada (ex: "1h", "30min")
- `room` (string): Nome da sala
- `observations` (string): Observações
- `status` (string): Status (default: "scheduled")
- `color` (string): Cor do evento (default: "bg-[#99ccff]")
- `service_id` (uuid): ID do serviço da tabela procedures
- `contact_id` (uuid): ID do contato da tabela clients
- `room_id` (uuid): ID da sala da tabela rooms

**Response**:
```json
{
  "success": true,
  "data": { /* appointment object */ },
  "message": "Appointment created successfully",
  "mode": "database"
}
```

**Cache Invalidation**:
- Invalida padrões: `ALL_APPOINTMENTS`, `CALENDAR_VIEWS`

---

### 3. **GET /appointments/[id]**
Busca um agendamento específico por ID.

**URL Parameters**:
- `id` (uuid): ID do agendamento

**Query Parameters**:
- `bypass_cache` (boolean): Bypass do cache

**Response**:
```json
{
  "success": true,
  "data": { /* appointment object */ },
  "mode": "database",
  "cached": false
}
```

---

### 4. **PUT /appointments/[id]**
Atualiza um agendamento existente.

**URL Parameters**:
- `id` (uuid): ID do agendamento

**Body**: Campos a serem atualizados (mesmos campos do POST)

**Response**:
```json
{
  "success": true,
  "data": { /* updated appointment */ },
  "message": "Appointment updated successfully",
  "mode": "database"
}
```

**Cache Invalidation**:
- Deleta cache específico do appointment
- Se `appointment_date` foi alterado: invalida `ALL_APPOINTMENTS` e `CALENDAR_VIEWS`

---

### 5. **DELETE /appointments/[id]**
Remove um agendamento (soft delete).

**URL Parameters**:
- `id` (uuid): ID do agendamento

**Behavior**: Atualiza `status` para "cancelled" (não deleta fisicamente)

**Response**:
```json
{
  "success": true,
  "message": "Appointment {id} deleted successfully",
  "mode": "database"
}
```

**Cache Invalidation**:
- Deleta cache específico
- Invalida: `ALL_APPOINTMENTS`, `CALENDAR_VIEWS`

---

## 🗄️ Database Schema Reference

### Procedures (Services)

**Exemplos de UUIDs válidos**:
```
659ee29a-ce0c-47a8-9f73-a56a02de137e  (Botox Facial - 30min - R$800)
05d89e1f-2065-479a-a46a-e1441ee8ad39  (Preenchimento Labial - 45min - R$1200)
2eaa4832-d877-4860-9402-0918b9da597f  (Limpeza de Pele - 60min - R$250)
143cee21-3b1d-4b7b-9448-92289b77915f  (Peeling Químico - 45min - R$350)
a19ac8a9-a231-494d-8928-ee4aeafa6a9b  (Microagulhamento - 60min - R$400)
```

**Structure**:
```sql
procedures (
  id UUID PRIMARY KEY,
  name VARCHAR UNIQUE,
  category VARCHAR,
  description TEXT,
  duration_minutes INT DEFAULT 60,
  price NUMERIC,
  active BOOLEAN DEFAULT true
)
```

---

## 🔄 Cache Strategy

**Cache Keys**:
- Appointments List: `appointments:list:{filters}`
- Appointment Detail: `appointment:detail:{id}`

**TTL**:
- List: 120 seconds (2 minutos)
- Detail: 300 seconds (5 minutos)

**Cache Patterns**:
- `ALL_APPOINTMENTS`: `appointments:*`
- `CALENDAR_VIEWS`: `calendar:*`

**Invalidation**:
- CREATE: Invalida todos os padrões
- UPDATE: Invalida específico + padrões se data mudou
- DELETE: Invalida específico + todos os padrões

---

## ⚙️ CORS & Headers

**CORS**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Cache Headers**:
```
Cache-Control: public, max-age={ttl}, stale-while-revalidate={swr}
ETag: "{timestamp}"
Vary: Accept-Encoding
```

---

## 🔒 Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request (missing required fields)
- `404`: Not Found
- `500`: Server Error

---

## 🧪 Example Usage

### Python (usando httpx)

```python
import httpx
from datetime import date, timedelta

BASE_URL = "https://clinica-luana-calendar-production.up.railway.app/api"

# Listar agendamentos de hoje
async def list_today_appointments():
    today = date.today().isoformat()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/appointments",
            params={"date": today}
        )
        return response.json()

# Criar agendamento
async def create_appointment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/appointments",
            json={
                "client_name": "Maria Silva",
                "client_phone": "+5594991398585",
                "appointment_date": "2025-10-25",
                "start_time": "14:00",
                "end_time": "15:00",
                "procedure": "Botox Facial",
                "treatment": "Harmonização Facial",
                "service_id": "659ee29a-ce0c-47a8-9f73-a56a02de137e",
                "room": "Sala 1"
            }
        )
        return response.json()

# Listar slots disponíveis (range de 7 dias)
async def list_available_range():
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=7)).isoformat()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/appointments",
            params={
                "start_date": start,
                "end_date": end
            }
        )
        return response.json()
```

---

## 📝 Notes

1. **Mock Mode**: API funciona em mock mode se Supabase não estiver configurado
2. **Soft Delete**: DELETE não remove fisicamente, apenas muda status para "cancelled"
3. **Cache**: Sistema de cache Redis integrado com invalidação inteligente
4. **CORS**: Permite todas as origens (configurar em produção se necessário)
5. **UUIDs**: Sempre use UUIDs válidos do banco para service_id, contact_id, room_id

---

**Última Atualização**: 2025-10-20  
**Versão da API**: 1.0  
**Repositório**: https://github.com/axisvitor/clinica-luana-calendar
