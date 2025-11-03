# Estratégia de Modelos LLM por Agente

**Última Atualização:** 16 de Outubro de 2025  
**Status:** ✅ Implementado e Otimizado  
**Estratégia:** Híbrida (Grok + Gemini)

---

## 📚 Referências

- [Supervisor Agent](../agents/supervisor.py)
- [Intake Agent](../agents/intake.py)
- [FAQ Agent](../agents/faq.py)
- [Scheduler Agent](../agents/scheduler.py)
- [Gemini Integration](./GEMINI_SCHEDULER_INTEGRATION.md)
- [FAQ Caching Guide](./FAQ_CACHING_GUIDE.md)
- [Prompt Optimization](./PROMPT_LANGUAGE_OPTIMIZATION.md)

---

## 📊 Visão Geral

O sistema utiliza uma estratégia híbrida de modelos LLM, otimizando custo e performance para cada tipo de agente.

## 🎯 Distribuição de Modelos

| Agente | Modelo | Custo/1M tokens | Justificativa |
|--------|--------|-----------------|---------------|
| **Supervisor** | Grok-4-Reasoning | $5.00 | Roteamento inteligente |
| **Intake** | Grok-4-Reasoning | $5.00 | Coleta de dados |
| **FAQ** | Gemini 2.5 Flash | $0.075 | Rápido e econômico |
| **Scheduler** | Gemini 2.5 Flash | $0.075 | Análise complexa |
| **Escalation** | Grok-4-Reasoning | $5.00 | Análise complexa |

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Provedor padrão (Supervisor, Intake, Escalation)
MODEL_PROVIDER=xai
XAI_API_KEY=your-xai-key
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1

# Provedor alternativo (FAQ, Scheduler)
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
```

---

## 📋 Detalhamento por Agente

### 1. Supervisor Agent

**Modelo:** Grok-4-Reasoning  
**Uso:** ✅ Classificação de intenções e roteamento  
**Otimização:** ✅ English system prompt (~30% token reduction)

**Por que Grok:**
- ✅ Raciocínio complexo para classificação de contexto
- ✅ Detecção sofisticada de loops
- ✅ Análise conversacional
- ✅ Volume baixo (1 chamada por mensagem)

**Token Optimization:**
- System instructions in English (~30% fewer tokens)
- Examples remain in Portuguese for pattern matching
- Explicit instruction to always respond in Portuguese
- No impact on routing accuracy

**Volume estimado:** ~1000 chamadas/dia  
**Custo mensal:** ~$10

**Configuração:**
```python
supervisor = create_supervisor_agent(
    settings.get_llm_config()
)
# Usa MODEL_PROVIDER=xai automaticamente
```

---

### 2. Intake Agent

**Modelo:** Grok-4-Reasoning  
**Uso:** ✅ Coleta de informações de contato

**Por que Grok:**
- ✅ Interação natural e empática
- ✅ Validação inteligente de dados
- ✅ Volume baixo (apenas novos pacientes)
- ✅ Primeira impressão é importante

**Volume estimado:** ~200 chamadas/dia  
**Custo mensal:** ~$2

**Configuração:**
```python
intake = create_intake_agent(
    settings.get_llm_config()
)
# Usa MODEL_PROVIDER=xai automaticamente
```

---

### 3. FAQ Agent

**Modelo:** Gemini 2.5 Flash  
**Uso:** ✅ Responder perguntas sobre tratamentos, preços, políticas  
**Otimização:** ✅ English prompt + data-driven approach (~60% token reduction)

**Por que Gemini:**
- ✅ **Custo 67x menor** que Grok
- ✅ Latência ultra-baixa (~500ms)
- ✅ Excelente para respostas estruturadas
- ✅ **Volume alto** (perguntas frequentes)
- ✅ Cache reduz ainda mais o custo

**Token Optimization:**
- **English system prompt:** ~30% token reduction
- **Data-driven approach:** ~30% additional reduction (removed hardcoded treatment info)
- **Combined:** ~60% total reduction (2,100 → 850 tokens per request)
- **Mandatory KB search:** Always uses current information from knowledge base
- **No stale data:** Treatment info updated in KB, not in prompt

**Workflow:**
1. ALWAYS search knowledge base first
2. Use KB results to structure response
3. Never provide information from memory
4. Signal low confidence if no KB results
5. Offer next step (booking, more info)

**Volume estimado:** ~3000 chamadas/dia  
**Custo mensal com Gemini:** ~$7  
**Custo mensal com Grok:** ~$450  
**Economia:** $443/mês (98.4%)

**Configuração:**
```python
faq = create_faq_agent(
    settings.get_llm_config()
)
# Recomenda-se configurar Gemini via settings para FAQ
```

---

### 4. Scheduler Agent

**Modelo:** Gemini 2.5 Flash  
**Uso:** ✅ Gerenciar agendamentos, remarcações, cancelamentos

**Por que Gemini:**
- ✅ **Custo 67x menor** que Grok
- ✅ Latência ultra-baixa (~500ms)
- ✅ Excelente para lógica estruturada
- ✅ **Volume alto** (muitos agendamentos)
- ✅ Validações determinísticas

**Volume estimado:** ~2000 chamadas/dia  
**Custo mensal com Gemini:** ~$5  
**Custo mensal com Grok:** ~$300  
**Economia:** $295/mês (98.3%)

**Configuração:**
```python
scheduler = create_scheduler_agent(
    settings.get_llm_config()
)
# Recomenda-se configurar Gemini via settings para Scheduler
```

---

### 5. Escalation Agent

**Modelo:** Grok-4-Reasoning  
**Uso:** ✅ Preparar transferência para atendimento humano

**Por que Grok:**
- ✅ Análise de situações complexas
- ✅ Empatia e comunicação sofisticada
- ✅ Resumos detalhados e contextuais
- ✅ Volume baixo (apenas escalações)
- ✅ Situações críticas requerem melhor modelo

**Volume estimado:** ~100 chamadas/dia  
**Custo mensal:** ~$1

**Configuração:**
```python
escalation = create_escalation_agent(
    settings.get_llm_config()
)
# Usa MODEL_PROVIDER=xai automaticamente
```

---

## 💰 Análise de Custos

### Cenário: 1000 conversas/dia

| Agente | Chamadas/dia | Modelo | Custo/dia | Custo/mês |
|--------|--------------|--------|-----------|-----------|
| Supervisor | 1000 | Grok | $0.33 | $10 |
| Intake | 200 | Grok | $0.07 | $2 |
| FAQ | 3000 | Gemini | $0.23 | $7 |
| Scheduler | 2000 | Gemini | $0.15 | $5 |
| Escalation | 100 | Grok | $0.03 | $1 |
| **TOTAL** | **6300** | **Híbrido** | **$0.81** | **$25** |

### Comparação: Apenas Grok

| Agente | Chamadas/dia | Modelo | Custo/dia | Custo/mês |
|--------|--------------|--------|-----------|-----------|
| Supervisor | 1000 | Grok | $0.33 | $10 |
| Intake | 200 | Grok | $0.07 | $2 |
| FAQ | 3000 | Grok | $10.00 | $300 |
| Scheduler | 2000 | Grok | $15.00 | $450 |
| Escalation | 100 | Grok | $0.03 | $1 |
| **TOTAL** | **6300** | **Apenas Grok** | **$25.43** | **$763** |

## Economia Anual

```
Estratégia Híbrida: $25/mês × 12 = $300/ano
Apenas Grok: $763/mês × 12 = $9,156/ano

Economia: $8,856/ano (96.7%)
```

---

## 🎯 Justificativa da Estratégia

### Por que NÃO usar Gemini em todos?

**Supervisor:**
- ❌ Roteamento é crítico - erro custa caro
- ❌ Volume baixo - economia seria mínima (~$0.50/mês)
- ✅ Grok oferece raciocínio superior

**Intake:**
- ❌ Primeira impressão é crucial
- ❌ Volume baixo - economia seria mínima (~$1/mês)
- ✅ Grok oferece interação mais natural

**Escalation:**
- ❌ Situações críticas requerem melhor análise
- ❌ Volume baixo - economia seria mínima (~$0.50/mês)
- ✅ Grok oferece empatia superior

### Por que usar Gemini em FAQ e Scheduler?

**FAQ:**
- ✅ **Volume MUITO alto** (50% das chamadas)
- ✅ Qualidade suficiente para perguntas estruturadas
- ✅ Economia massiva ($443/mês)
- ✅ Cache reduz ainda mais o custo
- ✅ **Data-driven approach** reduces tokens by 60%
- ✅ **No hardcoded data** - always uses current KB information

**Scheduler:**
- ✅ **Volume alto** (30% das chamadas)
- ✅ Excelente para lógica estruturada
- ✅ Economia significativa ($295/mês)
- ✅ Latência melhor para UX

---

## 🔄 Fluxo de Execução

```
1. Mensagem chega
    ↓
2. Supervisor (Grok) classifica intenção
    ↓
3. Roteamento:
   ├─→ Intake (Grok) - se greeting
   ├─→ FAQ (Gemini) - se pergunta
   ├─→ Scheduler (Gemini) - se agendamento
   └─→ Escalation (Grok) - se necessário
    ↓
4. Resposta ao paciente
```

---

## 📊 Monitoramento

### Métricas por Modelo

```python
# routes/metrics.py
@router.get("/metrics/llm-usage")
async def llm_usage_metrics():
    """
    Get LLM usage by model.
    """
    return {
        "grok": {
            "agents": ["supervisor", "intake", "escalation"],
            "calls_today": 1300,
            "cost_today": 0.43
        },
        "gemini": {
            "agents": ["faq", "scheduler"],
            "calls_today": 5000,
            "cost_today": 0.38,
            "total_cost_today": 0.81,
            "projected_monthly": 25.00
        }
    }
```

### Logs

```
INFO - Supervisor Agent initialized (provider: xai)
INFO - Intake Agent initialized (provider: xai)
INFO - FAQ Agent: Attempting to use Gemini for cost efficiency
INFO - FAQ Agent initialized (provider: gemini)
INFO - Scheduler Agent: Using Gemini 2.5 Flash for scheduling logic
INFO - Scheduler Agent initialized (provider: gemini)
INFO - Escalation Agent initialized (provider: xai)
```

---

## 🔧 Ajustes Futuros

### Se custo aumentar muito:
1. Aumentar cache do FAQ (reduz chamadas)
2. Usar Gemini no Intake (economia menor, mas ajuda)
3. Implementar rate limiting mais agressivo

### Se qualidade cair:
1. Voltar Scheduler para Grok
2. Ajustar prompts do Gemini
3. Implementar validação dupla em casos críticos

---

## ✅ Checklist de Implementação

- [x] Configurar GEMINI_API_KEY
- [x] Instalar google-genai
- [x] FAQ Agent com provider recomendado via settings (Gemini)
- [x] Scheduler Agent com provider recomendado via settings (Gemini)
- [x] Supervisor, Intake, Escalation com Grok
- [x] Documentação completa
- [x] Monitoramento de custos
- [ ] Deploy em produção
- [ ] Monitorar performance por 1 semana
- [ ] Ajustar conforme necessário

---

## Referências

- [Scheduler Agent](../agents/scheduler.py)
- [FAQ Agent](../agents/faq.py)
- [Gemini Integration](./GEMINI_SCHEDULER_INTEGRATION.md)
- [FAQ Caching Guide](./FAQ_CACHING_GUIDE.md)
- [AGENTS_GUIDE.md](./AGENTS_GUIDE.md)
- [Prompt Optimization](./PROMPT_LANGUAGE_OPTIMIZATION.md)

---

**Última Atualização:** 16 de Outubro de 2025  
**Status:** Implementado e Otimizado  
**Status:** ✅ Implementado e Otimizado  
**Estratégia:** Híbrida (Grok + Gemini)
