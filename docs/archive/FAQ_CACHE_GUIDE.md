# FAQ Cache - Guia Completo

## 📊 Visão Geral

O FAQ Agent agora inclui um sistema de cache inteligente que armazena respostas para perguntas frequentes, reduzindo custos de LLM e melhorando a latência de resposta.

**Benefícios**:
- ⚡ **Latência reduzida**: Respostas instantâneas para perguntas em cache
- 💰 **Economia de custos**: Menos chamadas ao LLM
- 📈 **Melhor experiência**: Respostas mais rápidas para pacientes
- 🎯 **Inteligente**: Normalização de perguntas para melhor matching

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Habilitar/desabilitar cache
FAQ_CACHE_ENABLED=true

# Tempo de vida do cache (segundos)
FAQ_CACHE_TTL_SECONDS=3600  # 1 hora

# Tamanho máximo do cache (número de entradas)
FAQ_CACHE_MAX_SIZE=100
```

### Valores Recomendados

| Ambiente | TTL | Max Size | Motivo |
|----------|-----|----------|--------|
| Produção | 3600 (1h) | 100 | Balanceado |
| Staging | 1800 (30min) | 50 | Testes |
| Dev | 600 (10min) | 20 | Desenvolvimento |

---

## 🎯 Como Funciona

### 1. Normalização de Perguntas

O cache normaliza perguntas para melhorar o matching:

```python
# Estas perguntas geram a MESMA chave de cache:
"Quanto custa a depilação a laser?"
"Qual o valor da depilação a laser?"
"Quanto é a depilação a laser"
"QUANTO CUSTA A DEPILAÇÃO A LASER?!"

# Todas são normalizadas para:
"preço depilação laser"
```

**Normalizações aplicadas**:
- Conversão para minúsculas
- Remoção de pontuação
- Substituição de sinônimos comuns
- Remoção de espaços extras

### 2. Armazenamento Seletivo

**Apenas respostas de alta confiança são cacheadas**:

```python
# ✅ Será cacheada
{
    "answer": "A depilação a laser...",
    "confidence": "high",
    "should_escalate": false
}

# ❌ NÃO será cacheada
{
    "answer": "Não tenho certeza...",
    "confidence": "low",
    "should_escalate": true
}
```

### 3. Expiração Automática (TTL)

Entradas expiram automaticamente após o TTL configurado:

```
Entrada criada: 10:00
TTL: 3600s (1 hora)
Expira em: 11:00
```

### 4. Limite de Tamanho

Quando o cache atinge o tamanho máximo, as entradas mais antigas são removidas:

```
Max Size: 100
Entradas: 100
Nova entrada → Remove a mais antiga
```

---

## 📈 Métricas de Cache

### Obter Estatísticas

```python
from agents.faq import create_faq_agent

agent = create_faq_agent(llm_config, enable_cache=True)

# Obter estatísticas
stats = agent.get_cache_stats()

print(stats)
# {
#     "size": 45,
#     "max_size": 100,
#     "hits": 120,
#     "misses": 30,
#     "hit_rate": 0.8,  # 80%
#     "ttl_seconds": 3600
# }
```

### Métricas Importantes

**Hit Rate (Taxa de Acerto)**:
```
hit_rate = hits / (hits + misses)

Exemplo:
- Hits: 120
- Misses: 30
- Hit Rate: 120 / 150 = 0.8 (80%)
```

**Interpretação**:
- < 30%: Cache pouco efetivo (considerar desabilitar)
- 30-50%: Razoável
- 50-70%: Bom
- > 70%: Excelente

---

## 🚀 Uso

### Criação do Agente

```python
from agents.faq import create_faq_agent

# Com cache habilitado (padrão)
agent = create_faq_agent(
    llm_config,
    enable_cache=True,
    cache_ttl_seconds=3600,
    cache_max_size=100
)

# Sem cache
agent = create_faq_agent(
    llm_config,
    enable_cache=False
)
```

### Responder Perguntas

```python
# Primeira vez - vai ao LLM
result1 = await agent.answer_question("Quanto custa a depilação a laser?")
print(result1["cached"])  # False

# Segunda vez - vem do cache
result2 = await agent.answer_question("Quanto custa a depilação a laser?")
print(result2["cached"])  # True

# Pergunta similar - também vem do cache
result3 = await agent.answer_question("Qual o valor da depilação a laser?")
print(result3["cached"])  # True
```

### Limpar Cache

```python
# Limpar todo o cache
agent.clear_cache()

# Verificar
stats = agent.get_cache_stats()
print(stats["size"])  # 0
```

### Warm-up do Cache

```python
from agents.faq import COMMON_FAQ_QUESTIONS

# Pré-popular cache com perguntas comuns
agent.warm_cache(COMMON_FAQ_QUESTIONS)

# Verificar
stats = agent.get_cache_stats()
print(f"Cache warmed with {stats['size']} entries")
```

---

## 📋 Perguntas Comuns Pré-definidas

O sistema inclui 15 perguntas comuns para warm-up:

```python
COMMON_FAQ_QUESTIONS = [
    "Quanto custa a depilação a laser?",
    "Qual o horário de funcionamento?",
    "Onde fica a clínica?",
    "Vocês fazem harmonização facial?",
    "Qual a política de cancelamento?",
    "Quantas sessões de laser preciso fazer?",
    "Depilação a laser dói?",
    "Quais são as contraindicações do botox?",
    "Posso fazer laser grávida?",
    "Quanto custa harmonização facial?",
    "Vocês trabalham com Mounjaro?",
    "Tem apartamento para pós-operatório?",
    "Quanto custa o apartamento?",
    "Como funciona a criolipólise?",
    "Vocês fazem preenchimento labial?",
]
```

---

## 🔍 Monitoramento

### Logs

O cache gera logs estruturados:

```
INFO - FAQ cache enabled: TTL=3600s, max_size=100
INFO - FAQ cache HIT: question='Quanto custa a depilação...', hit_rate=75.0%
DEBUG - FAQ cached: question='Quanto custa a depilação...', cache_size=45
DEBUG - Cleaned up 5 expired cache entries
DEBUG - Removed 10 oldest cache entries
INFO - FAQ cache cleared
```

### Métricas no Dashboard

Adicionar ao dashboard de métricas:

```python
# routes/metrics.py
@router.get("/metrics/faq-cache")
async def faq_cache_metrics():
    """Get FAQ cache metrics."""
    from services.agent_orchestrator import get_faq_agent
    
    agent = get_faq_agent()
    stats = agent.get_cache_stats()
    
    if not stats:
        return {"cache_enabled": False}
    
    return {
        "cache_enabled": True,
        "size": stats["size"],
        "max_size": stats["max_size"],
        "hits": stats["hits"],
        "misses": stats["misses"],
        "hit_rate": stats["hit_rate"],
        "hit_rate_percent": f"{stats['hit_rate'] * 100:.1f}%",
        "ttl_seconds": stats["ttl_seconds"],
        "ttl_hours": stats["ttl_seconds"] / 3600
    }
```

---

## 💡 Melhores Práticas

### 1. TTL Apropriado

**Muito curto** (< 30 min):
- ❌ Cache pouco efetivo
- ❌ Mais chamadas ao LLM
- ✅ Informações sempre atualizadas

**Balanceado** (1-2 horas):
- ✅ Bom equilíbrio
- ✅ Cache efetivo
- ✅ Informações razoavelmente atualizadas

**Muito longo** (> 4 horas):
- ✅ Cache muito efetivo
- ❌ Risco de informações desatualizadas
- ❌ Mudanças de preço/política demoram a refletir

**Recomendação**: 1-2 horas para produção

### 2. Tamanho do Cache

**Muito pequeno** (< 50):
- ❌ Entradas removidas frequentemente
- ❌ Hit rate baixo
- ✅ Uso mínimo de memória

**Balanceado** (50-150):
- ✅ Bom equilíbrio
- ✅ Hit rate razoável
- ✅ Uso moderado de memória

**Muito grande** (> 200):
- ✅ Hit rate alto
- ❌ Uso excessivo de memória
- ❌ Cleanup mais lento

**Recomendação**: 100 entradas para produção

### 3. Warm-up em Produção

```python
# main.py - durante startup
from agents.faq import create_faq_agent, COMMON_FAQ_QUESTIONS

# Criar agente
faq_agent = create_faq_agent(llm_config, enable_cache=True)

# Warm-up cache (opcional, mas recomendado)
if settings.is_production:
    logger.info("Warming FAQ cache...")
    faq_agent.warm_cache(COMMON_FAQ_QUESTIONS)
    logger.info("FAQ cache warmed")
```

### 4. Monitoramento Contínuo

Monitorar hit rate regularmente:

```python
# Alertar se hit rate < 30%
stats = agent.get_cache_stats()
if stats and stats["hit_rate"] < 0.3:
    logger.warning(
        f"FAQ cache hit rate baixo: {stats['hit_rate']:.1%}. "
        f"Considerar ajustar TTL ou tamanho."
    )
```

### 5. Invalidação Manual

Quando informações mudam (preços, políticas):

```python
# Limpar cache após atualização de preços
agent.clear_cache()
logger.info("Cache cleared after price update")

# Opcional: Re-warm com novas informações
agent.warm_cache(COMMON_FAQ_QUESTIONS)
```

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes de cache
pytest tests/test_faq_cache.py -v

# Teste específico
pytest tests/test_faq_cache.py::test_cache_hit_rate -v

# Com cobertura
pytest tests/test_faq_cache.py --cov=agents.faq --cov-report=html
```

### Testes Incluídos

- ✅ Inicialização do cache
- ✅ Geração de chaves
- ✅ Normalização de perguntas
- ✅ Set e Get
- ✅ Cache miss
- ✅ Apenas alta confiança
- ✅ Expiração TTL
- ✅ Limite de tamanho
- ✅ Hit rate
- ✅ Estatísticas
- ✅ Limpeza
- ✅ Matching de similaridade

---

## 📊 Impacto Esperado

### Redução de Custos

Assumindo:
- 1000 perguntas/dia
- Hit rate de 70%
- Custo por pergunta: $0.001

**Sem cache**:
```
1000 perguntas × $0.001 = $1.00/dia
$1.00 × 30 dias = $30.00/mês
```

**Com cache (70% hit rate)**:
```
300 perguntas ao LLM × $0.001 = $0.30/dia
$0.30 × 30 dias = $9.00/mês

Economia: $21.00/mês (70%)
```

### Redução de Latência

**Sem cache**:
- Latência média: 2-3 segundos (chamada LLM)

**Com cache**:
- Cache hit: < 50ms
- Cache miss: 2-3 segundos

**Latência média com 70% hit rate**:
```
(0.7 × 0.05s) + (0.3 × 2.5s) = 0.035s + 0.75s = 0.785s

Redução: 68% na latência média
```

---

## 🔧 Troubleshooting

### Problema: Hit Rate Baixo (< 30%)

**Causas possíveis**:
1. Perguntas muito variadas
2. TTL muito curto
3. Cache muito pequeno
4. Normalização insuficiente

**Soluções**:
```bash
# Aumentar TTL
FAQ_CACHE_TTL_SECONDS=7200  # 2 horas

# Aumentar tamanho
FAQ_CACHE_MAX_SIZE=200

# Verificar logs de normalização
```

### Problema: Respostas Desatualizadas

**Causa**: TTL muito longo

**Solução**:
```bash
# Reduzir TTL
FAQ_CACHE_TTL_SECONDS=1800  # 30 minutos

# Ou limpar cache manualmente após atualizações
```

### Problema: Uso Excessivo de Memória

**Causa**: Cache muito grande

**Solução**:
```bash
# Reduzir tamanho máximo
FAQ_CACHE_MAX_SIZE=50

# Ou desabilitar cache
FAQ_CACHE_ENABLED=false
```

---

## 📚 Referências

- [agents/faq.py](../agents/faq.py) - Implementação do cache
- [tests/test_faq_cache.py](../tests/test_faq_cache.py) - Testes
- [config/settings.py](../config/settings.py) - Configurações

---

**Última Atualização**: 16 de Outubro de 2025  
**Versão**: 1.0.0  
**Status**: ✅ Implementado e Testado
