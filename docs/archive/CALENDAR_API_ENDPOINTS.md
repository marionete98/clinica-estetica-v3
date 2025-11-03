# 📡 Endpoints da API do Sistema de Calendário

## Base URL
```
https://clinica-luana-calendar-production.up.railway.app/api
```

## 🔍 Endpoints Disponíveis

### 1. Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "clinica-luana-calendar",
  "version": "1.0.0",
  "timestamp": "2025-10-16T10:30:00Z",
  "features": {
    "appointments": true,
    "whatsapp": false,
    "database": "mock",
    "cache": false
  }
}
```

---

### 2. Appointments - Listar

```http
GET /appointments
GET /appointments?date=2025-10-16
GET /appointments?start_date=2025-10-16&end_date=2025-10-20
GET /appointments?bypass_cache=true
```

**Query Parameters:**
- `date` (opcional): Data específica (YYYY-MM-DD)
- `start_date` (opcional): Data inicial do período
- `end_date` (opcional): Data final do período
- `bypass_cache` (opcional): true para ignorar cache

**Resposta:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "client_name": "Maria Silva",
      "client_phone": "+5511999999999",
      "client_email": "maria@email.com",
      "appointment_date": "2025-10-16",
      "start_time": "09:00",
      "end_time": "10:00",
      "duration": "1h",
      "procedure": "Ácido Hialurônico",
      "treatment": "Harmonização facial",
      "room": "Sala 01",
      "observations": "Primeira consulta",
      "status": "scheduled",
      "whatsapp_sent": false,
      "whatsapp_sent_at": null,
      "reminder_sent": false,
      "reminder_sent_at": null,
      "color": "bg-[#ff9999]",
      "created_at": "2025-10-15T10:00:00Z",
      "updated_at": "2025-10-15T10:00:00Z"
    }
  ],
  "count": 1,
  "mode": "database",
  "cached": false
}
```

---

### 3. Appointments - Criar

```http
POST /appointments
Content-Type: application/json
```

**Body (campos obrigatórios):**
```json
{
  "client_name": "João Santos",
  "appointment_date": "2025-10-17",
  "start_time": "14:00",
  "end_time": "15:00",
  "procedure": "Botox",
  "treatment": "Harmonização facial"
}
```

**Body (completo com opcionais):**
```json
{
  "client_name": "João Santos",
  "client_phone": "+5511888888888",
  "client_email": "joao@email.com",
  "appointment_date": "2025-10-17",
  "start_time": "14:00",
  "end_time": "15:00",
  "duration": "1h",
  "procedure": "Botox",
  "treatment": "Harmonização facial",
  "room": "Sala 02",
  "observations": "Cliente novo",
  "status": "scheduled",
  "color": "bg-[#99ccff]"
}
```

**Resposta (sucesso):**
```json
{
  "success": true,
  "data": {
    "id": "new-uuid",
    "client_name": "João Santos",
    ...
  },
  "message": "Appointment created successfully",
  "mode": "database"
}
```

---

### 4. Appointments - Buscar por ID

```http
GET /appointments/{id}
GET /appointments/{id}?bypass_cache=true
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "client_name": "Maria Silva",
    ...
  },
  "mode": "database",
  "cached": false
}
```

---

### 5. Appointments - Atualizar

```http
PUT /appointments/{id}
Content-Type: application/json
```

**Body (apenas campos a atualizar):**
```json
{
  "status": "confirmed",
  "observations": "Cliente confirmou por WhatsApp",
  "whatsapp_sent": true
}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    ...
  },
  "message": "Appointment updated successfully",
  "mode": "database"
}
```

---

### 6. Appointments - Deletar (Soft Delete)

```http
DELETE /appointments/{id}
```

**Nota:** Marca o appointment como `cancelled` ao invés de deletar fisicamente.

**Resposta:**
```json
{
  "success": true,
  "message": "Appointment {id} deleted successfully",
  "mode": "database"
}
```

---

### 7. Cache - Gerenciamento

```http
GET /cache
GET /cache?action=health
GET /cache?action=stats
GET /cache?action=warmup
```

**Resposta (health):**
```json
{
  "success": true,
  "health": {
    "enabled": true,
    "size": 42,
    "hitRate": 0.85
  }
}
```

**POST /cache - Operações:**
```json
{
  "action": "set",
  "key": "custom_key",
  "value": {...},
  "ttl": 300
}
```

```json
{
  "action": "get",
  "key": "custom_key"
}
```

```json
{
  "action": "invalidate",
  "pattern": "appointments:*"
}
```

**DELETE /cache - Limpar:**
```http
DELETE /cache?all=true
DELETE /cache?pattern=appointments:*
DELETE /cache?key=specific_key
```

---

### 8. Notifications - Enviar WhatsApp

```http
POST /notifications/send-whatsapp
Content-Type: application/json
```

**Body:**
```json
{
  "appointment_id": "uuid",
  "notification_type": "confirmation",
  "phone_override": "+5511999999999"
}
```

**Tipos de notificação:**
- `confirmation` - Confirmação de agendamento
- `reminder` - Lembrete (24h antes)
- `cancellation` - Cancelamento
- `rescheduled` - Remarcação

**Resposta:**
```json
{
  "success": true,
  "message": "WhatsApp notification sent successfully",
  "data": {
    "appointment_id": "uuid",
    "phone": "+5511999999999",
    "notification_type": "confirmation",
    "message_id": "whatsapp-msg-id"
  }
}
```

**Nota:** Requer Evolution API configurada (EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_NAME)

---

### 9. Notifications - Push Notifications

```http
POST /notifications/send
Content-Type: application/json
```

**Body:**
```json
{
  "subscription": {
    "endpoint": "...",
    "keys": {
      "p256dh": "...",
      "auth": "..."
    }
  },
  "title": "Lembrete de Consulta",
  "body": "Sua consulta é amanhã às 14:00",
  "icon": "/icons/icon-192x192.png",
  "data": {
    "url": "/appointments/uuid"
  }
}
```

**Nota:** Requer VAPID keys configuradas

---

## 📊 Status dos Appointments

- `scheduled` - Agendado (padrão)
- `confirmed` - Confirmado
- `completed` - Concluído
- `cancelled` - Cancelado
- `no_show` - Não compareceu

---

## 🎨 Cores Disponíveis

- `bg-[#ff9999]` - Rosa claro
- `bg-[#99ccff]` - Azul claro (padrão)
- `bg-[#99ff99]` - Verde claro
- `bg-[#ffff99]` - Amarelo claro
- `bg-[#ffcc99]` - Laranja claro
- `bg-[#d6a4ff]` - Roxo claro

---

## 🔒 Autenticação

**Status Atual:** Sem autenticação (desenvolvimento)
**CORS:** Habilitado para todas origens
**Rate Limiting:** Não implementado

---

## ⚠️ Notas Importantes

1. **Cache:** Sistema usa cache in-memory com TTL configurável
2. **Soft Delete:** DELETE marca como cancelled ao invés de remover
3. **Timezone:** Todos horários em UTC-3 (Brasília)
4. **WhatsApp:** Requer Evolution API configurada
5. **Push:** Requer VAPID keys configuradas

---

## 🔧 Integração com Sistema de IA

### Exemplo Python:
```python
import httpx
from datetime import datetime, timedelta

class CalendarAPIClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_appointments(self, date: str = None):
        url = f"{self.base_url}/appointments"
        params = {"date": date} if date else {}
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def create_appointment(self, data: dict):
        url = f"{self.base_url}/appointments"
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    async def update_appointment(self, appointment_id: str, updates: dict):
        url = f"{self.base_url}/appointments/{appointment_id}"
        response = await self.client.put(url, json=updates)
        response.raise_for_status()
        return response.json()
    
    async def cancel_appointment(self, appointment_id: str):
        url = f"{self.base_url}/appointments/{appointment_id}"
        response = await self.client.delete(url)
        response.raise_for_status()
        return response.json()
```

---

**Última atualização:** 16/10/2025
**Repositório:** https://github.com/axisvitor/clinica-luana-calendar.git
