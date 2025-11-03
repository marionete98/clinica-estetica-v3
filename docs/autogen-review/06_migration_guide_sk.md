# Guia de Migração: Agentes para Semantic Kernel

Este guia detalha o processo passo a passo para migrar os agentes de `OpenAIChatCompletionClient` (legado) para `SKChatCompletionAdapter` com Semantic Kernel.

## Pré-requisitos
- `semantic-kernel==1.18.1` instalado (✅ adicionado ao requirements.txt)
- `google-generativeai` removido (✅ removido do requirements.txt)
- `openai==1.105.0` presente (usado para Grok via base_url)

## Ordem de Migração Recomendada
1. **FAQ Agent** (maior benefício: Gemini para reasoning)
2. **Intake Agent** (baixo risco, fluxo simples)
3. **Scheduler Agent** (médio risco, lógica complexa de agendamento)
4. **Supervisor Agent** (crítico: routing de intents)
5. **Escalation Agent** (baixo risco, fluxo de escalação)

## Template de Migração

### Passo 1: Atualizar Imports

**Antes:**
```python
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
```

**Depois:**
```python
from openai import AsyncOpenAI

from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIChatCompletion,
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
```

### Passo 2: Refatorar `_create_model_client`

**Antes (exemplo FAQ):**
```python
def _create_model_client(self) -> OpenAIChatCompletionClient:
    provider = self.llm_config.get("provider", "xai")
    
    if provider == "xai":
        return OpenAIChatCompletionClient(
            model=self.llm_config.get("model", "grok-beta"),
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config.get("base_url", "https://api.x.ai/v1"),
            model_info=ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                family="grok",
            ),
        )
    # ... outros providers
```

**Depois:**
```python
def _create_model_client(self) -> SKChatCompletionAdapter:
    """Create model client using Semantic Kernel."""
    provider = self.llm_config.get("provider", "xai")
    
    if provider == "gemini":
        # Gemini via SK GoogleAI connector
        sk_client = GoogleAIChatCompletion(
            gemini_model_id=self.llm_config.get("model", "gemini-1.5-flash"),
            api_key=self.llm_config["api_key"],
        )
        prompt_settings = GoogleAIChatPromptExecutionSettings(
            temperature=self.llm_config.get("temperature", 0.7),
            max_output_tokens=self.llm_config.get("max_tokens", 2048),
        )
    elif provider == "xai":
        # Grok via SK OpenAI connector + AsyncOpenAI base_url
        async_client = AsyncOpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config.get("base_url", "https://api.x.ai/v1"),
        )
        sk_client = OpenAIChatCompletion(
            ai_model_id=self.llm_config.get("model", "grok-2"),
            async_client=async_client,
        )
        prompt_settings = OpenAIChatPromptExecutionSettings(
            temperature=self.llm_config.get("temperature", 0.7),
            max_tokens=self.llm_config.get("max_tokens", 2048),
        )
    elif provider == "openai":
        # OpenAI (opcional/legado)
        async_client = AsyncOpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config.get("base_url", "https://api.openai.com/v1"),
        )
        sk_client = OpenAIChatCompletion(
            ai_model_id=self.llm_config.get("model", "gpt-4o-mini"),
            async_client=async_client,
        )
        prompt_settings = OpenAIChatPromptExecutionSettings(
            temperature=self.llm_config.get("temperature", 0.7),
            max_tokens=self.llm_config.get("max_tokens", 2048),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Wrap SK client com SKChatCompletionAdapter para AutoGen
    return SKChatCompletionAdapter(
        sk_client,
        kernel=Kernel(memory=NullMemory()),
        prompt_settings=prompt_settings,
    )
```

### Passo 3: Atualizar Type Hints

**Antes:**
```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

class FAQAgent:
    def __init__(self, llm_config: Dict[str, Any]):
        self.model_client: OpenAIChatCompletionClient = self._create_model_client()
```

**Depois:**
```python
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

class FAQAgent:
    def __init__(self, llm_config: Dict[str, Any]):
        self.model_client: SKChatCompletionAdapter = self._create_model_client()
```

## Checklist de Migração por Agente

### Para cada agente (`agents/faq.py`, `agents/intake.py`, etc.):

- [ ] Backup do arquivo original
- [ ] Atualizar imports (adicionar SK, remover ModelInfo se não usado)
- [ ] Refatorar `_create_model_client()` conforme template
- [ ] Atualizar type hints
- [ ] Rodar linter (black, flake8, mypy)
- [ ] Testar localmente:
  - [ ] Provider `gemini` funciona
  - [ ] Provider `xai` funciona
  - [ ] Provider `openai` (se suportado) funciona
  - [ ] Tools ainda funcionam corretamente
  - [ ] Cleanup funciona (sem leaks de recursos)
- [ ] Executar testes unitários existentes
- [ ] Executar testes de integração
- [ ] Commit com mensagem descritiva: `feat(agents): migrate {agent_name} to Semantic Kernel`

## Configuração de Ambiente

### `.env` (exemplo):
```bash
# Provider padrão (xai ou gemini)
MODEL_PROVIDER=gemini

# Gemini (Google AI)
GEMINI_API_KEY=your_google_ai_key_here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_BASE_URL=  # Opcional, SK usa padrão

# Grok (xAI)
XAI_API_KEY=your_xai_key_here
XAI_MODEL=grok-2
XAI_BASE_URL=https://api.x.ai/v1

# OpenAI (opcional/legado)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Testes Recomendados

### Teste 1: Criação do Cliente
```python
import asyncio
from agents.faq import create_faq_agent

async def test_faq_sk_creation():
    llm_config = {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "api_key": "test_key",
    }
    
    agent = create_faq_agent(llm_config)
    assert agent.model_client is not None
    assert isinstance(agent.model_client, SKChatCompletionAdapter)
    
    await agent.cleanup()

asyncio.run(test_faq_sk_creation())
```

### Teste 2: Resposta Real (integração)
```python
async def test_faq_sk_answer():
    import os
    llm_config = {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
    }
    
    agent = create_faq_agent(llm_config)
    result = await agent.answer_question("Quanto custa depilação a laser?")
    
    assert result["answer"]
    assert result["confidence"] in ["high", "low"]
    
    await agent.cleanup()

asyncio.run(test_faq_sk_answer())
```

## Rollback Plan

Se houver problemas após a migração:

1. **Rollback imediato (git):**
   ```bash
   git revert <commit_hash>
   git push
   ```

2. **Feature flag (recomendado para produção):**
   Adicionar flag `USE_SEMANTIC_KERNEL` em `config/settings.py`:
   ```python
   class Settings(BaseSettings):
       use_semantic_kernel: bool = Field(default=False, env="USE_SEMANTIC_KERNEL")
   ```
   
   No agente:
   ```python
   def _create_model_client(self):
       if settings.use_semantic_kernel:
           return self._create_sk_client()
       else:
           return self._create_legacy_client()
   ```

## Referências
- Exemplos completos: `docs/autogen-review/05_examples_sk.md`
- Findings: `docs/autogen-review/01_findings.md`
- Fix plan: `docs/autogen-review/03_fix_plan.md`
- Semantic Kernel docs: https://learn.microsoft.com/en-us/semantic-kernel/
- AutoGen + SK integration: https://microsoft.github.io/autogen/stable/reference/python/autogen_ext.models.semantic_kernel.html

## Notas Importantes
- **Não migrar todos de uma vez**: Fazer PR separado para cada agente
- **Testar em dev primeiro**: Validar completamente antes de prod
- **Monitorar logs**: Checar se não há errors/warnings de SK após deploy
- **Performance**: SK pode ter latência ligeiramente diferente; monitorar métricas
- **Custos**: Gemini e Grok têm preços diferentes; revisar custos após migração completa
