# Configuration Guide

**Data:** 16 de Outubro de 2025  
**Status:** ✅ **ATUALIZADO**

---

## 🎯 **Visão Geral**

O sistema de configuração da Clínica Luana utiliza `pydantic-settings` para gerenciar todas as variáveis de ambiente de forma type-safe e validada.

---

## 📁 **Estrutura de Configuração**

### **Arquivo Principal**
- `config/settings.py` - Classe Settings com todas as configurações
- `.env.example` - Template com todas as variáveis disponíveis
- `.env` - Arquivo local com suas credenciais (não commitado)

### **Singleton Pattern**
```python
# ✅ Uso correto - instância singleton
from config.settings import settings

# Acessar configurações
provider = settings.model_provider
api_key = settings.xai_api_key
```

---

## 🔧 **Propriedades de Configuração**

### **1. LLM Configuration**

#### **Provider Selection**
```python
# Lowercase (recomendado)
settings.model_provider  # 'xai' | 'gemini'

# Uppercase (compatibilidade)
settings.MODEL_PROVIDER  # 'XAI' | 'GEMINI'
```

#### **xAI Grok**
```python
settings.xai_api_key      # API key
settings.xai_model        # 'grok-4-reasoning'
settings.xai_base_url     # 'https://api.x.ai/v1'
```

#### **Google Gemini**
```python
settings.gemini_api_key   # API key
settings.gemini_model     # 'gemini-2.5-flash'
```

#### **LLM Config Helper**
```python
# Retorna configuração completa baseada no provider
config = settings.get_llm_config()
# {
#   "provider": "xai",
#   "api_key": "sk-...",
#   "model": "grok-4-reasoning",
#   "base_url": "https://api.x.ai/v1",
#   "timeout": 10
# }
```

### **2. Environment Configuration**

#### **Environment Detection**
```python
# Lowercase (recomendado)
settings.env  # 'development' | 'staging' | 'production'

# Uppercase (compatibilidade)
settings.ENV  # 'DEVELOPMENT' | 'STAGING' | 'PRODUCTION'

# Helper properties
settings.is_production    # bool
settings.is_development   # bool
```

### **3. Database Configuration**

#### **Supabase**
```python
settings.supabase_url         # Project URL
settings.supabase_key         # Service role key
settings.supabase_jwt_secret  # JWT secret (optional)
```

#### **Redis**
```python
settings.redis_url       # Connection URL
settings.redis_password  # Password (optional)
settings.redis_host      # Host (optional)
settings.redis_port      # Port (default: 6379)
```

### **4. External Services**

#### **Chatwoot**
```python
settings.chatwoot_api_url        # API base URL
settings.chatwoot_account_id     # Account ID
settings.chatwoot_api_token      # API token
settings.chatwoot_webhook_secret # Webhook secret
```

#### **Calendar API**
```python
settings.calendar_api_url     # External calendar API
settings.calendar_api_timeout # Request timeout (default: 10s)
```

### **5. Application Settings**

#### **Agent Configuration**
```python
settings.max_tool_calls_per_session  # Default: 3
settings.response_timeout_seconds    # Default: 10
settings.max_context_messages        # Default: 20
```

#### **Rate Limiting**
```python
settings.max_requests_per_minute  # Default: 100
```

#### **Message Processing**
```python
settings.message_dedup_ttl_seconds        # Default: 300 (5 min)
settings.message_processing_delay_seconds # Default: 7
```

#### **FAQ Cache**
```python
settings.faq_cache_enabled      # Default: True
settings.faq_cache_ttl_seconds  # Default: 3600 (1 hour)
settings.faq_cache_max_size     # Default: 100
```

### **6. Business Rules**

#### **Business Hours**
```python
settings.business_hours_start    # Default: "08:30"
settings.business_hours_end      # Default: "19:00"
settings.business_hours_sat_end  # Default: "12:00"
```

#### **Booking Policies**
```python
settings.min_booking_advance_hours   # Default: 1
settings.harmonization_cancel_hours  # Default: 4
settings.laser_cancel_hours          # Default: 24
settings.max_reschedule_count        # Default: 2
```

#### **Reminders**
```python
settings.reminder_d1_hours_before  # Default: 24
settings.reminder_h2_hours_before  # Default: 2
```

### **7. Monitoring**

#### **Thresholds**
```python
settings.p95_latency_threshold_ms        # Default: 7000
settings.error_rate_threshold_percent    # Default: 2.0
settings.handover_rate_threshold_percent # Default: 30.0
```

#### **Alerts**
```python
settings.alert_email          # Email for alerts
settings.enable_email_alerts  # Default: False
```

---

## 🔍 **Validação de Configuração**

### **Validação Automática**

O sistema valida automaticamente:

1. **Provider Keys**: Verifica se a chave API está presente para o provider selecionado
2. **Type Safety**: Todos os tipos são validados pelo Pydantic
3. **Required Fields**: Campos obrigatórios são verificados no startup

### **Validação Manual**

```python
# Validar configuração completa
try:
    from config.settings import settings
    config = settings.get_llm_config()
    print("✅ Configuração válida")
except ValueError as e:
    print(f"❌ Erro de configuração: {e}")
```

### **Script de Validação**

```bash
# Validar todas as configurações
python scripts/validate_env.py
```

---

## 🚀 **Uso em Produção**

### **Environment Variables**

```bash
# Essenciais para produção
ENV=production
MODEL_PROVIDER=xai
XAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=...
REDIS_URL=redis://...
CHATWOOT_API_URL=https://...
CHATWOOT_API_TOKEN=...
```

### **Railway Deployment**

```bash
# Configurar variáveis no Railway
railway variables set ENV=production
railway variables set MODEL_PROVIDER=xai
railway variables set XAI_API_KEY=sk-...
# ... outras variáveis
```

---

## 🔄 **Backward Compatibility**

### **Propriedades Uppercase**

Para compatibilidade com código legado, as seguintes propriedades estão disponíveis:

```python
# Novo (recomendado)
settings.model_provider  # 'xai'
settings.env            # 'production'

# Legado (compatibilidade)
settings.MODEL_PROVIDER  # 'XAI'
settings.ENV            # 'PRODUCTION'
```

### **Migration Guide**

Se você tem código usando as propriedades uppercase, pode continuar funcionando:

```python
# ✅ Ambos funcionam
if settings.ENV == 'PRODUCTION':
    pass

if settings.env == 'production':
    pass
```

---

## 📝 **Exemplos de Uso**

### **1. Configuração de Agent**

```python
from config.settings import settings

def create_agent():
    llm_config = settings.get_llm_config()
    
    return Agent(
        name="FAQ Agent",
        llm_config=llm_config,
        max_tool_calls=settings.max_tool_calls_per_session,
        timeout=settings.response_timeout_seconds
    )
```

### **2. Verificação de Ambiente**

```python
from config.settings import settings

def setup_logging():
    if settings.is_production:
        level = "INFO"
    else:
        level = "DEBUG"
    
    logging.basicConfig(level=level)
```

### **3. Configuração Condicional**

```python
from config.settings import settings

def get_cache_config():
    if settings.faq_cache_enabled:
        return {
            "ttl": settings.faq_cache_ttl_seconds,
            "max_size": settings.faq_cache_max_size
        }
    return None
```

---

## 🛠️ **Troubleshooting**

### **Erros Comuns**

#### **1. Missing API Key**
```
ValueError: XAI_API_KEY is required when MODEL_PROVIDER is set to 'xai'
```
**Solução**: Definir `XAI_API_KEY` no ambiente

#### **2. Invalid Provider**
```
ValueError: Unsupported model provider: invalid
```
**Solução**: Usar 'xai' ou 'gemini' para `MODEL_PROVIDER`

#### **3. Type Validation Error**
```
ValidationError: Input should be a valid integer
```
**Solução**: Verificar tipos das variáveis numéricas

### **Debug Configuration**

```python
from config.settings import settings
import json

# Imprimir configuração (sem secrets)
config = {
    "provider": settings.model_provider,
    "env": settings.env,
    "cache_enabled": settings.faq_cache_enabled,
    "business_hours": {
        "start": settings.business_hours_start,
        "end": settings.business_hours_end
    }
}

print(json.dumps(config, indent=2))
```

---

## 📚 **Referências**

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Environment Variables Best Practices](https://12factor.net/config)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)

---

## 🎉 **Conclusão**

O sistema de configuração oferece:

- ✅ **Type Safety** com Pydantic
- ✅ **Validação Automática** no startup
- ✅ **Backward Compatibility** com propriedades uppercase
- ✅ **Environment Detection** com helpers
- ✅ **LLM Config Helper** para fácil integração
- ✅ **Comprehensive Coverage** de todas as configurações

**O sistema está pronto para produção com configuração robusta e flexível!** 🚀

---

**Atualizado por:** Kiro AI Assistant  
**Data:** 16 de Outubro de 2025  
**Status:** ✅ DOCUMENTAÇÃO COMPLETA