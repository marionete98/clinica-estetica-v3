# 📋 Configuração - Guia Compacto

## 🚀 Início Rápido

### 1. Clone e Instale
```bash
git clone https://github.com/axisvitor/clinica-luana-calendar.git
cd clinica-luana-calendar
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Configure Variáveis de Ambiente

**Arquivo**: `.env` (copie de `.env.example`)

```env
# LLM Providers
MODEL_PROVIDER=xai                    # 'xai' ou 'gemini'
XAI_API_KEY=your_xai_key             # Para xAI Grok
GEMINI_API_KEY=your_gemini_key       # Para Google Gemini (opcional)

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Redis
REDIS_URL=redis://username:password@host:port

# Chatwoot Integration
CHATWOOT_API_URL=https://your-chatwoot.com
CHATWOOT_ACCOUNT_ID=your_account_id
CHATWOOT_API_TOKEN=your_token
CHATWOOT_WEBHOOK_SECRET=your_secret

# Railway (Produção)
RAILWAY_STATIC_URL=https://your-app.railway.app
```

### 3. Valide Configuração
```bash
python scripts/validate_env.py
```

### 4. Execute
```bash
uvicorn main:app --reload  # Desenvolvimento
# ou
python main.py             # Produção
```

---

## 📋 Variáveis Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MODEL_PROVIDER` | Provider LLM principal | `xai` ou `gemini` |
| `XAI_API_KEY` | Chave xAI Grok | `xai-xxxxx` |
| `SUPABASE_URL` | URL do Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Chave Supabase | `eyJxxx...` |
| `REDIS_URL` | URL Redis completa | `redis://user:pass@host:port` |
| `CHATWOOT_*` | Integração Chatwoot | URLs e tokens |

---

## 🔧 Configurações Avançadas

### LLM por Agente
```python
# Em services/agent_orchestrator.py

def _get_faq_llm_config(self):
    return {
        "provider": "gemini",           # FAQ usa Gemini
        "model": "gemini-1.5-flash",
        "api_key": settings.GEMINI_API_KEY,
    }

def _get_scheduler_llm_config(self):
    return {
        "provider": "xai",              # Scheduler usa Grok
        "model": "grok-beta",
        "api_key": settings.XAI_API_KEY,
    }
```

### Contexto Adaptativo
```python
# Máximo de mensagens por agente
MAX_CONTEXT = {
    "supervisor": 3,    # Classificação rápida
    "intake": 3,        # Coleta rápida
    "faq": 4,          # Respostas simples
    "scheduler": 6,    # Fluxo de agendamento
    "escalation": 10,  # Resumo completo
}
```

---

## 🚨 Troubleshooting

### Problema: `ModuleNotFoundError`
```bash
pip install autogen-ext[semantic-kernel]==0.4.0
pip install semantic-kernel==1.18.1
```

### Problema: Redis Connection Failed
```bash
# Verificar se Redis está rodando
redis-cli ping

# Verificar URL no .env
echo $REDIS_URL
```

### Problema: Chatwoot Webhook 401
```bash
# Verificar secret no .env
grep CHATWOOT_WEBHOOK_SECRET .env

# Testar webhook manualmente
curl -X POST https://your-app/webhook/chatwoot \
  -H "X-Chatwoot-Signature: test" \
  -d '{"event":"message_created","content":"test"}'
```

---

## 📚 Arquivos Relacionados

- [📖 Configuração Completa](./CONFIGURATION_GUIDE.md) - Versão detalhada
- [🧠 Estratégia LLM](./LLM_STRATEGY_BY_AGENT.md) - Estratégia por agente
- [🔄 Migração SK](./SEMANTIC_KERNEL_MIGRATION.md) - Migração técnica

---

**Versão**: v3.0
**Última Atualização**: 2025-10-20
**Status**: ✅ **Produção-Ready**
