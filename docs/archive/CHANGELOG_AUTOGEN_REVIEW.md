# Changelog - AutoGen Review & Semantic Kernel Migration

## [2025-10-20] - Fase 1: Preparação e Correções P1

### ✅ Adicionado
- **Semantic Kernel 1.18.1** ao `requirements.txt` para integração com Gemini e Grok
- **Documentação completa** em `docs/autogen-review/`:
  - `00_status_e_proximos_passos.md` - Status e roadmap
  - `01_findings.md` - Auditoria técnica e issues
  - `02_checklist.md` - Checklist de conformidade
  - `03_fix_plan.md` - Plano de correções
  - `04_versions.md` - Matriz de versões
  - `05_examples_sk.md` - Exemplos Gemini + Grok via SK
  - `06_migration_guide_sk.md` - Guia de migração passo a passo

### ✅ Corrigido
- **Strings UTF-8 corrompidas** em 5 arquivos:
  - `main.py`: "Cl?nica" → "Clínica" (docstrings, logs, títulos)
  - `agents/intake.py`: Acentuação em prompts ("Oli" → "Olá", "informaoAes" → "informações", etc.)
  - `routes/webhooks.py`: Logs com ruído ("I Waiting" → "⏳ Aguardando", etc.)
  - `utils/guardrails.py`: Docstring corrigido

- **Lazy validation em `config/settings.py`**:
  - Validação de chaves LLM agora condicional a `ENV=production`
  - `model_post_init()` e `@model_validator()` apenas em prod
  - Permite testes e dev sem chaves LLM completas

- **Async Supabase em `tools/scheduler_tools.py`**:
  - Substituídas 2 chamadas síncronas bloqueantes
  - `supabase.table().execute()` → `await supabase_ops.aselect()`
  - Linhas ~270-290 e ~395-406

### ❌ Removido
- **google-generativeai 0.8.5** do `requirements.txt` (deprecado, não usado)

### 📊 Métricas
- **Issues P1 resolvidos:** 4/4 (100%)
- **Arquivos de código modificados:** 7
- **Arquivos de documentação criados/atualizados:** 7
- **Testes de sintaxe:** ✅ Passou

### 🎯 Impacto
- **UX:** Mensagens e logs com acentuação correta
- **Dev:** Testes rodam sem configuração LLM completa
- **Performance:** Event loop não bloqueado por Supabase síncrono
- **Preparação:** Stack 100% pronto para migração SK

### 📝 Notas Técnicas

#### Semantic Kernel - Configuração Padrão
```python
# Gemini (Google AI)
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion
sk_client = GoogleAIChatCompletion(
    gemini_model_id="gemini-1.5-flash",
    api_key=os.environ["GOOGLE_AI_API_KEY"]
)

# Grok (xAI via OpenAI-compatible)
from openai import AsyncOpenAI
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
async_client = AsyncOpenAI(
    api_key=os.environ["XAI_API_KEY"],
    base_url="https://api.x.ai/v1"
)
sk_client = OpenAIChatCompletion(
    ai_model_id="grok-2",
    async_client=async_client
)

# AutoGen Integration
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
model_client = SKChatCompletionAdapter(
    sk_client,
    kernel=Kernel(memory=NullMemory()),
    prompt_settings=prompt_settings
)
```

#### Lazy Validation - Comportamento
- **ENV=development/staging:** Chaves LLM opcionais no import
- **ENV=production:** Chaves LLM obrigatórias (valida no import)
- **get_llm_config():** Sempre valida quando chamado (em qualquer ENV)

### 🔜 Próximas Fases

#### Fase 2: Migração de Agentes para SK (Pendente)
**Ordem:** FAQ → Intake → Scheduler → Supervisor → Escalation

Para cada agente:
1. Branch separado (ex: `feat/migrate-faq-agent-to-sk`)
2. Atualizar imports (SK connectors)
3. Refatorar `_create_model_client()` conforme `06_migration_guide_sk.md`
4. Testar (gemini + xai + tools + cleanup)
5. PR com testes

#### Fase 3: Issues P2 (Pendente)
- `reflect_on_tool_use=True` em FAQ/Scheduler
- Timezone consistente (America/Sao_Paulo)
- Taxonomia KB uniforme
- Migrar `/chat` para DI pattern

### 📚 Referências
- **Guia migração SK:** `docs/autogen-review/06_migration_guide_sk.md`
- **Status completo:** `docs/autogen-review/00_status_e_proximos_passos.md`
- **Exemplos:** `docs/autogen-review/05_examples_sk.md`

---

**Data:** 2025-10-20  
**Autor:** AI Assistant + Equipe Dev  
**Validação:** Sintaxe Python ✅ | Testes unitários 🟡 Pendente
