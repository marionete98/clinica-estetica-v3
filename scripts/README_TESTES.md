# 🧪 Guia de Testes dos Agentes

## Scripts de Teste Disponíveis

### 1. Teste Completo de Todos os Agentes
**Script:** `scripts/test_all_agents_complete.py`

**Descrição:**
Valida inicialização, configuração e funcionalidade básica de todos os 6 agentes do sistema.

**Execução:**
```bash
py scripts/test_all_agents_complete.py
```

**O que testa:**
- ✅ Supervisor: Roteamento e classificação de intenção
- ✅ FAQ: Cache Redis, model client, knowledge base
- ✅ Intake: Acolhimento, WhatsApp implícito, sem coleta de dados
- ✅ Scheduler: Ferramentas de agendamento, calendar integration
- ✅ Escalation: Critérios de escalação, handoff para humanos
- ✅ FollowUp: Acompanhamento pós-atendimento

**Resultado Esperado:**
```
✓ Sistema de agentes está funcionando corretamente!
Agentes aprovados: 6/6 (100.0%)
Testes aprovados: 21/21 (100.0%)
```

---

### 2. Testes Unitários com Pytest

**Execução:**
```bash
# Todos os testes
py -m pytest tests/ -v

# Testes específicos
py -m pytest tests/test_config.py -v
py -m pytest tests/test_tools.py -v
py -m pytest tests/test_validators.py -v

# Com cobertura
py -m pytest --cov=agents --cov=services --cov=tools tests/
```

**Nota:** Requer variáveis de ambiente configuradas (`.env` file)

---

### 3. Testes E2E (End-to-End)

**Scripts disponíveis:**
- `tests/test_e2e.py` - Fluxo completo de conversação
- `tests/test_e2e_complete.py` - Cenários estendidos
- `tests/test_conversations.py` - Múltiplos cenários de conversa

**Execução:**
```bash
py -m pytest tests/test_e2e.py -v -s
```

---

## Configuração de Ambiente para Testes

### Variáveis de Ambiente Necessárias

Crie um arquivo `.env.test` ou configure as seguintes variáveis:

```bash
# LLM Providers
XAI_API_KEY=your_xai_key
GEMINI_API_KEY=your_gemini_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis
REDIS_URL=redis://localhost:6379

# Chatwoot
CHATWOOT_API_URL=your_chatwoot_url
CHATWOOT_ACCOUNT_ID=1
CHATWOOT_API_TOKEN=your_token

# Calendar (opcional para alguns testes)
CALENDAR_API_KEY=your_calendar_key
```

---

## Estrutura de Testes

```
tests/
├── test_all_agents_complete.py  # ✅ Teste completo (novo)
├── test_config.py               # Configurações
├── test_tools.py                # Ferramentas de agendamento
├── test_validators.py           # Validadores
├── test_e2e.py                  # Testes end-to-end
├── test_conversations.py        # Cenários de conversa
├── test_scheduler_refactored.py # Scheduler específico
├── test_intake_optimized.py     # Intake específico
└── test_faq_cache.py            # Cache do FAQ
```

---

## Interpretação de Resultados

### ✅ Status PASS
- Agente inicializado corretamente
- Todos os atributos essenciais presentes
- Funcionalidades específicas validadas

### ✗ Status FAIL
- Erro na inicialização
- Atributos faltando
- Configuração incorreta

**Exemplo de saída:**
```
╭──────────┬──────────┬────────┬─────────────────────╮
│ Agente   │ Status   │ Testes │ Detalhes            │
├──────────┼──────────┼────────┼─────────────────────┤
│ FAQ      │ ✓ PASS   │ 4/4    │ Cache OK, agent OK  │
│ Intake   │ ✓ PASS   │ 4/4    │ WhatsApp OK         │
└──────────┴──────────┴────────┴─────────────────────┘
```

---

## Troubleshooting

### Erro: "missing required positional argument"
**Causa:** Tentativa de inicializar agente diretamente sem factory function  
**Solução:** Use `create_*_agent(llm_config)` ao invés de `Agent()`

### Erro: "ValidationError: Field required"
**Causa:** Variáveis de ambiente não configuradas  
**Solução:** Configure `.env` com todas as variáveis necessárias

### Erro: "Cannot import name"
**Causa:** Dependências não instaladas  
**Solução:** `pip install -r requirements.txt`

---

## Testes de Qualidade de Prompts (Agent Lightning)

### APO Training
**Script:** `scripts/train_apo_complete.py`

Otimiza prompts dos agentes usando Agent Lightning APO (Automatic Prompt Optimization).

**Execução (Linux/WSL):**
```bash
cd /mnt/c/exclusivo/clinica-estetica-v3
source venv_linux/bin/activate
python scripts/train_apo_complete.py
```

**Requisitos:**
- `agentlightning==0.2.1`
- Linux/WSL (APO não funciona no Windows)
- OPENAI_API_KEY ou XAI_API_KEY

---

## Métricas de Sucesso

### Baseline Atual (03/11/2025)
- **Supervisor:** 100% (3/3 testes)
- **FAQ:** 100% (4/4 testes)
- **Intake:** 100% (4/4 testes)
- **Scheduler:** 100% (4/4 testes)
- **Escalation:** 100% (3/3 testes)
- **FollowUp:** 100% (3/3 testes)

**Total:** 21/21 testes passando (100%)

---

## Próximos Testes Recomendados

1. **Performance Testing**
   - Tempo de resposta < 2s por agente
   - Throughput: 100 req/min
   - Cache hit rate > 70% (FAQ)

2. **Load Testing**
   - Múltiplas conversas simultâneas
   - Stress test com 1000+ mensagens

3. **Quality Testing**
   - LLM-as-judge para avaliar respostas
   - Satisfação do usuário > 4.5/5
   - Taxa de escalação < 10%

4. **Integration Testing**
   - Chatwoot webhooks
   - Calendar API
   - Supabase persistence
   - Redis cache

---

## Comandos Úteis

```bash
# Executar teste rápido
py scripts/test_all_agents_complete.py

# Pytest com verbose
py -m pytest tests/ -v --tb=short

# Pytest com coverage
py -m pytest --cov=. --cov-report=html tests/

# Apenas testes rápidos (não E2E)
py -m pytest tests/ -m "not slow"

# Parar no primeiro erro
py -m pytest tests/ -x

# Executar teste específico
py -m pytest tests/test_faq_cache.py::test_cache_hit -v
```

---

**Última Atualização:** 03/11/2025  
**Versão:** 1.0  
**Autor:** Sistema de Testes Automatizados
