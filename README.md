# 🏥 Clínica Luana - Sistema Multi-Agente

**Sistema de atendimento automatizado via WhatsApp com múltiplos agentes especializados**

[![Status](https://img.shields.io/badge/Status-Produção-success)](https://github.com/axisvitor/clinica-luana)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-AutoGen%20%2B%20Semantic%20Kernel-orange)](https://microsoft.github.io/autogen/)

---

## 🚀 Início Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/axisvitor/clinica-luana-calendar.git
cd clinica-luana-calendar

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Execute
uvicorn main:app --reload
```

📖 **Documentação Completa**: [`docs/README.md`](./docs/README.md)

---

## 🤖 Agentes Disponíveis

| Agente | Função | LLM |
|--------|--------|-----|
| **Supervisor** | Classifica intent e roteia | xAI/Gemini |
| **Intake** | Coleta dados iniciais | xAI/Gemini |
| **FAQ** | Responde perguntas | Gemini |
| **Scheduler** | Gerencia agendamentos | Gemini |
| **Escalation** | Prepara escalação humana | xAI/Gemini |
| **Followup** | Mensagens automáticas | xAI/Gemini |

📖 **Detalhes**: [`docs/AGENTS_GUIDE_COMPACT.md`](./docs/AGENTS_GUIDE_COMPACT.md)

---

## 🏗️ Arquitetura

```
WhatsApp → Chatwoot → FastAPI Gateway → Agent Orchestrator
                                              ↓
                                    ┌─────────┴─────────┐
                                    │                   │
                              Supervisor          Context Manager
                                    │                   │
                    ┌───────────────┼───────────────┐   │
                    ↓               ↓               ↓   ↓
                 Intake           FAQ          Scheduler
                    │               │               │
                    └───────────────┴───────────────┘
                                    ↓
                            Escalation/Followup
                                    ↓
                            Response → Chatwoot → WhatsApp
```

**Componentes:**
- **Redis**: Cache de contexto (24h TTL)
- **Supabase**: Persistência de dados
- **Calendar API**: Sistema de agendamentos (Next.js)
- **Chatwoot**: Integração WhatsApp

📖 **Contexto**: [`docs/CONTEXTO_SISTEMA.md`](./docs/CONTEXTO_SISTEMA.md)

---

## 📋 Documentação Essencial

### 🚀 **Setup e Deploy**
- [Configuração Rápida](./docs/CONFIGURATION_GUIDE_COMPACT.md)
- [Deploy no Railway](./docs/RAILWAY_QUICKSTART.md)
- [Checklist de Deploy](./docs/DEPLOYMENT_CHECKLIST.md)

### 🤖 **Desenvolvimento**
- [Guia de Agentes](./docs/AGENTS_GUIDE_COMPACT.md)
- [Estratégia LLM](./docs/LLM_STRATEGY_BY_AGENT.md)
- [Migração Semantic Kernel](./docs/SEMANTIC_KERNEL_MIGRATION.md)
- [Refatoração Scheduler](./docs/SCHEDULER_REFACTORING_COMPLETE.md)

### 🔧 **Integrações**
- [Chatwoot Integration](./docs/CHATWOOT_INTEGRATION_GUIDE.md)
- [Calendar API](./docs/CALENDAR_API_DOCS.md)
- [Base de Conhecimento](./docs/KB_TOOLS_CACHED_GUIDE.md)

### 🛡️ **Qualidade**
- [Error Handling](./docs/ERROR_HANDLING_GUIDE.md)
- [Guardrails](./docs/GUARDRAILS_GUIDE.md)
- [Observabilidade](./docs/OBSERVABILITY_QUICKSTART.md)
- [Relatório de Testes](./docs/TESTING_REPORT.md)

📚 **Índice Completo**: [`docs/DOCUMENTATION_INDEX.md`](./docs/DOCUMENTATION_INDEX.md)

---

## 🎯 Status do Projeto

| Componente | Status | Última Atualização |
|------------|--------|-------------------|
| **Agentes** | ✅ 6/6 migrados para SK | 2025-10-20 |
| **Calendar API** | ✅ Integrado e funcional | 2025-10-20 |
| **Scheduler** | ✅ Refatorado | 2025-10-20 |
| **Testes** | ✅ 100% passando | 2025-10-20 |
| **Deploy** | ✅ Pronto para Railway | 2025-10-20 |
| **Documentação** | ✅ Organizada | 2025-10-20 |

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=app tests

# Teste específico do scheduler refatorado
python test_scheduler_refactored.py
```

📊 **Cobertura Atual**: 85%+

---

## 🌐 Deploy

### **Railway (Produção)**
```bash
# Via Railway CLI
railway up

# Ou via GitHub (automático)
git push origin main
```

### **Variáveis de Ambiente Obrigatórias**
```env
MODEL_PROVIDER=xai
XAI_API_KEY=your_key
GEMINI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
REDIS_URL=redis://...
CHATWOOT_API_URL=your_url
CHATWOOT_API_TOKEN=your_token
```

📖 **Guia Completo**: [`docs/RAILWAY_QUICKSTART.md`](./docs/RAILWAY_QUICKSTART.md)

---

## 📞 Suporte

- **Repositório**: https://github.com/axisvitor/clinica-luana-calendar
- **Documentação**: [`docs/`](./docs/)
- **Issues**: [GitHub Issues](https://github.com/axisvitor/clinica-luana-calendar/issues)

---

## 📝 Licença

Projeto privado - Clínica Luana

---

**Versão**: v3.0 - Produção Ready  
**Última Atualização**: 2025-10-20  
**Status**: 🚀 **PRONTO PARA DEPLOY**
