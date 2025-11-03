# 🚨 Análise de Risco: Respostas JSON aos Usuários
**Data:** Outubro 2025  
**Criticidade:** 🔴 **ALTA**  
**Status:** ⚠️ **VULNERÁVEL**

---

## 📋 Sumário Executivo

**PROBLEMA IDENTIFICADO:** O sistema tem **ALTO RISCO** de enviar respostas em formato JSON aos usuários finais no WhatsApp.

### Problemas Críticos Encontrados

1. 🔴 **`json_output=True` em TODOS os agentes** (7 agentes afetados)
2. 🔴 **Sem sanitização JSON antes de enviar ao Chatwoot**
3. 🟠 **Prompts não proíbem explicitamente JSON**
4. 🟡 **Sem validação de formato de resposta**

---

## 🔍 Análise Detalhada

### 1. Configuração `json_output=True` (CRÍTICO)

**Localização:** Todos os agentes em `agents/`

```python
# agents/supervisor.py:130
model_info=ModelInfo(
    vision=False,
    function_calling=True,
    json_output=True,  # 🔴 PROBLEMA!
    family="grok",
)

# agents/faq.py:374
# agents/intake.py:125
# agents/scheduler.py:236
# agents/escalation.py:169
# agents/followup.py:225
```

**Impacto:**
- A flag `json_output=True` pode instruir o LLM a responder em formato JSON
- Modelos como GPT-4 e Gemini interpretam isso como "responda em JSON estruturado"
- Mesmo com prompts em português, o modelo pode retornar JSON

**Exemplo de resposta problemática:**
```json
{
  "response": "Olá! Como posso ajudar?",
  "confidence": "high",
  "intent": "greeting"
}
```

Ao invés de:
```
Olá! Como posso ajudar?
```

---

### 2. Fluxo de Resposta (Sem Sanitização)

**Caminho atual:**
```
Agent → response_data → orchestrator → webhooks → Chatwoot → WhatsApp
```

**Code flow:**
```python
# 1. Agent retorna (pode ser JSON!)
response_data = await self.faq.answer_question(...)

# 2. Orchestrator extrai (assume formato correto)
response_text = response_data.get("response", "")

# 3. Webhooks envia DIRETAMENTE (SEM sanitização!)
if response_text:
    await send_message_with_metadata(
        conversation_id=conversation_id,
        content=response_text,  # 🔴 Pode ser JSON aqui!
        ...
    )
```

**Problema:** Nenhuma etapa valida ou sanitiza JSON!

---

### 3. Response Parser (Parcialmente Seguro)

**Arquivo:** `utils/response_parser.py`

**O que faz BEM:**
```python
def safe_parse_response(response, agent_name, fallback):
    # ✅ Extrai conteúdo de objetos complexos
    # ✅ Converte para string
    # ✅ Faz .strip()
    # ✅ Trata vários formatos
```

**O que NÃO faz:**
```python
# ❌ Não detecta se conteúdo é JSON
# ❌ Não remove marcadores JSON
# ❌ Não valida formato de resposta humana
```

**Exemplo de falha:**
```python
# Se o LLM retornar:
content = '{"response": "Olá!", "intent": "greeting"}'

# O parser retorna EXATAMENTE isso (é uma string válida!)
return content.strip()  # Retorna o JSON como string!
```

---

### 4. Prompts dos Agentes (Proteção Parcial)

#### ✅ Pontos Positivos
```python
# Todos os prompts têm:
"**CRITICAL: Always respond to patients in Portuguese (Brazil).**"
```

#### ❌ Pontos Negativos
```python
# Nenhum prompt tem proteção explícita como:
"**NEVER respond in JSON format**"
"**ALWAYS respond in natural conversational text**"
"**Format: Plain text only, no code blocks, no JSON**"
```

---

## 🎯 Cenários de Falha

### Cenário 1: FAQ com JSON
```
Usuário: "Quanto custa depilação a laser?"

❌ Resposta do Agent (com json_output=True):
{
  "answer": "O valor da depilação a laser varia de R$ 80 a R$ 300",
  "category": "price",
  "confidence": 0.95
}

✅ Resposta esperada:
O valor da depilação a laser varia de R$ 80 a R$ 300 por sessão! 😊
```

### Cenário 2: Scheduler com JSON
```
Usuário: "Quero agendar amanhã às 10h"

❌ Resposta do Agent:
{
  "response": "Perfeito! Temos disponibilidade amanhã às 10h",
  "action": "booking_available",
  "slots": ["10:00", "10:30", "11:00"]
}

✅ Resposta esperada:
Perfeito! Temos disponibilidade amanhã às 10h. Confirma? 📅
```

### Cenário 3: Escalation com JSON
```
Usuário: "Quero falar com alguém"

❌ Resposta do Agent:
{
  "patient_message": "Vou conectar você com nossa equipe",
  "summary": "Cliente solicitou atendimento humano",
  "should_pause_automation": true
}

✅ Resposta esperada:
Vou conectar você com nossa equipe! Um momento... 🤝
```

---

## 🛡️ Soluções Propostas

### Solução 1: Remover `json_output=True` (RECOMENDADO)

**Prioridade:** 🔴 CRÍTICA  
**Esforço:** Baixo (10 minutos)  
**Impacto:** Alto

```python
# ANTES (PROBLEMA)
model_info=ModelInfo(
    vision=False,
    function_calling=True,
    json_output=True,  # ❌ Remove!
    family="grok",
)

# DEPOIS (CORRETO)
model_info=ModelInfo(
    vision=False,
    function_calling=True,
    json_output=False,  # ✅ Desabilita JSON output
    family="grok",
)
```

**Arquivos a modificar:**
- `agents/supervisor.py` (3 ocorrências - xai, gemini, openai)
- `agents/faq.py` (3 ocorrências)
- `agents/intake.py` (3 ocorrências)
- `agents/scheduler.py` (3 ocorrências)
- `agents/escalation.py` (3 ocorrências)
- `agents/followup.py` (3 ocorrências)

**Total:** 18 mudanças

---

### Solução 2: Adicionar Sanitização JSON

**Prioridade:** 🟠 ALTA  
**Esforço:** Médio (30 minutos)  
**Impacto:** Médio (proteção adicional)

Criar função de sanitização:

```python
# utils/response_sanitizer.py

import json
import re
import logging

logger = logging.getLogger(__name__)

def sanitize_json_response(response: str, agent_name: str) -> str:
    """
    Detect and extract text from JSON responses.
    
    This prevents JSON from being sent to users in WhatsApp.
    
    Args:
        response: Raw response text (may contain JSON)
        agent_name: Agent name for logging
        
    Returns:
        str: Clean text response without JSON formatting
    """
    if not response or not isinstance(response, str):
        return response
    
    response = response.strip()
    
    # Check if response looks like JSON
    if response.startswith('{') and response.endswith('}'):
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            logger.warning(
                f"{agent_name}: Detected JSON response, extracting text",
                extra={"raw_response": response[:200]}
            )
            
            # Extract text from common keys
            for key in ['response', 'answer', 'message', 'patient_message', 'content', 'text']:
                if key in data and isinstance(data[key], str):
                    extracted = data[key].strip()
                    logger.info(f"{agent_name}: Extracted '{key}' field from JSON")
                    return extracted
            
            # If no known key, log and return error message
            logger.error(
                f"{agent_name}: JSON response without extractable text field",
                extra={"json_keys": list(data.keys())}
            )
            return "Desculpe, tive um problema ao processar a resposta. Pode reformular sua pergunta?"
            
        except json.JSONDecodeError:
            # Not valid JSON, probably just text with { } characters
            pass
    
    # Check for JSON code blocks (```json ... ```)
    json_block_pattern = r'```json\s*\n(.*?)\n```'
    match = re.search(json_block_pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        logger.warning(f"{agent_name}: Detected JSON code block, removing formatting")
        json_content = match.group(1)
        try:
            data = json.loads(json_content)
            # Extract text from common keys
            for key in ['response', 'answer', 'message', 'patient_message']:
                if key in data and isinstance(data[key], str):
                    return data[key].strip()
        except json.JSONDecodeError:
            pass
        # Remove the code block but keep content
        response = re.sub(json_block_pattern, json_content, response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove any remaining code block markers
    response = re.sub(r'```\w*\n?', '', response)
    
    return response.strip()
```

**Uso no orchestrator:**

```python
# services/agent_orchestrator.py

from utils.response_sanitizer import sanitize_json_response

# Depois de extrair response_text (linha ~520):
response_text = response_data.get("response", "")

# ADICIONAR sanitização:
response_text = sanitize_json_response(response_text, agent_name)
```

---

### Solução 3: Fortalecer Prompts

**Prioridade:** 🟡 MÉDIA  
**Esforço:** Baixo (15 minutos)  
**Impacto:** Médio

Adicionar instruções explícitas em todos os prompts:

```python
# Adicionar no início de cada SYSTEM_PROMPT:

**RESPONSE FORMAT (CRITICAL):**
- ALWAYS respond in natural conversational Portuguese text
- NEVER use JSON format in your responses
- NEVER use code blocks (```)
- NEVER structure responses as {"key": "value"}
- Your response goes DIRECTLY to the patient via WhatsApp
- Format: Plain text only, use emojis for friendliness

**WRONG (DON'T DO THIS):**
{"response": "Olá! Como posso ajudar?"}

**CORRECT (DO THIS):**
Olá! Como posso ajudar? 😊
```

**Arquivos a modificar:**
- `agents/supervisor.py` - SUPERVISOR_SYSTEM_PROMPT
- `agents/faq.py` - FAQ_SYSTEM_PROMPT
- `agents/intake.py` - INTAKE_SYSTEM_PROMPT
- `agents/scheduler.py` - SCHEDULER_SYSTEM_PROMPT
- `agents/escalation.py` - ESCALATION_SYSTEM_PROMPT
- `agents/followup.py` - FOLLOWUP_SYSTEM_PROMPT

---

### Solução 4: Validação de Resposta

**Prioridade:** 🟢 BAIXA (Nice to have)  
**Esforço:** Médio (45 minutos)  
**Impacto:** Baixo (monitoramento)

Adicionar validação e alertas:

```python
# utils/response_validator.py

def validate_response_format(response: str, agent_name: str) -> tuple[bool, str]:
    """
    Validate that response is in proper format for users.
    
    Returns:
        tuple: (is_valid, issue_description)
    """
    if not response:
        return False, "empty_response"
    
    # Check for JSON structure
    if response.strip().startswith('{') and response.strip().endswith('}'):
        return False, "json_format"
    
    # Check for code blocks
    if '```' in response:
        return False, "code_block"
    
    # Check for common JSON keys
    json_indicators = ['"response":', '"answer":', '"message":']
    if any(indicator in response for indicator in json_indicators):
        return False, "json_structure"
    
    # Check minimum length (too short may indicate error)
    if len(response.strip()) < 10:
        return False, "too_short"
    
    return True, "valid"


# Uso no orchestrator:
from utils.response_validator import validate_response_format

is_valid, issue = validate_response_format(response_text, agent_name)
if not is_valid:
    logger.error(
        f"Invalid response format detected: {issue}",
        extra={
            "agent": agent_name,
            "response_preview": response_text[:100]
        }
    )
    # Opcionalmente usar fallback
```

---

## 🚀 Plano de Implementação

### Fase 1: Correção Urgente (HOJE)

1. ✅ **Remover `json_output=True`** (Solução 1)
   - Tempo: 10 minutos
   - Criticidade: MÁXIMA
   - Testar depois

### Fase 2: Proteção Adicional (ESTA SEMANA)

2. ✅ **Implementar sanitização JSON** (Solução 2)
   - Tempo: 30 minutos
   - Segurança adicional

3. ✅ **Fortalecer prompts** (Solução 3)
   - Tempo: 15 minutos
   - Prevenção proativa

### Fase 3: Monitoramento (PRÓXIMA SEMANA)

4. ✅ **Adicionar validação** (Solução 4)
   - Tempo: 45 minutos
   - Detectar problemas futuros

---

## 🧪 Testes Necessários

### Teste 1: FAQ Simple
```
Input: "Quanto custa botox?"
Esperado: Texto natural em português
Não esperado: JSON, code blocks
```

### Teste 2: Scheduler Flow
```
Input: "Quero agendar amanhã"
Esperado: Pergunta em texto natural
Não esperado: {"response": "..."}
```

### Teste 3: Escalation
```
Input: "Quero falar com alguém"
Esperado: Mensagem empática em texto
Não esperado: Objeto JSON
```

### Teste 4: Long Context
```
Input: Múltiplas mensagens seguidas
Esperado: Todas em texto natural
Não esperado: Falha no formato
```

---

## 📊 Análise de Risco

### Antes das Correções
- **Probabilidade:** 🔴 Alta (60-80%)
- **Impacto:** 🔴 Alto (UX ruim, cliente confuso)
- **Risco Total:** 🔴 **CRÍTICO**

### Depois da Solução 1
- **Probabilidade:** 🟡 Média (20-30%)
- **Impacto:** 🟠 Médio
- **Risco Total:** 🟡 **MÉDIO**

### Depois de Todas as Soluções
- **Probabilidade:** 🟢 Baixa (<5%)
- **Impacto:** 🟢 Baixo
- **Risco Total:** 🟢 **ACEITÁVEL**

---

## 🎯 Conclusão e Recomendações

### Conclusão

O sistema **ESTÁ VULNERÁVEL** a enviar respostas JSON aos usuários. A configuração `json_output=True` em todos os agentes é o principal problema.

### Recomendações Imediatas

1. 🔴 **URGENTE:** Remover `json_output=True` de todos os agentes
2. 🟠 **IMPORTANTE:** Implementar sanitização JSON
3. 🟡 **RECOMENDADO:** Fortalecer prompts com instruções explícitas

### Priorização

```
Prioridade 1 (HOJ E): Solução 1 (remover json_output)
Prioridade 2 (SEMANA): Soluções 2 e 3 (sanitização + prompts)
Prioridade 3 (FUTURO): Solução 4 (validação)
```

### Próximos Passos

1. Aplicar correções
2. Testar em staging
3. Monitorar logs após deploy
4. Validar com usuários reais

---

**Status Final:** ⚠️ **CORREÇÃO NECESSÁRIA ANTES DE PRODUÇÃO**

**Tempo para correção completa:** ~1h30min  
**Impacto se não corrigir:** 🔴 Usuários receberão JSON, péssima UX  
**Dificuldade da correção:** 🟢 Baixa

---

**Próxima ação:** Aplicar Solução 1 (remover `json_output=True`)
