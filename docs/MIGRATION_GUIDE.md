# Guia de Migração - Sistema Refatorado

## Mudanças Principais
- Configurações de LLM agora utilizam `config.llm_config.create_llm_config`.
- Repositório monolítico (`models/repository.py`) foi removido em favor de repositórios específicos em `models/repositories/`.
- Dependências externas (Redis, Supabase) agora expõem factories `get_*` para facilitar injection e testes.
- Camada de orquestração dividida em `conversation_manager`, `routing_engine` e `agent_coordinator`.

## Atualizando Código Existente

### LLM Configuration
```python
from config.llm_config import create_llm_config

llm_config = create_llm_config(
    provider="xai",
    model="grok-beta",
    api_key="...",
)
```

### Memory/Cache
```python
from services.memory import redis_memory_store
value = await redis_memory_store.get("key")
```

### Repositórios
```python
from models.repositories import get_contact_repository

contact_repo = get_contact_repository()
contact = await contact_repo.get_contact_by_phone(phone)
```

### Orchestrator
```python
from services.agent_orchestrator import create_orchestrator

orchestrator = await create_orchestrator()
try:
    result = await orchestrator.orchestrate(
        conversation_id="conv-123",
        phone="+5511999999999",
        message="Olá!"
    )
finally:
    await orchestrator.cleanup()
```

## Checklist
- [x] Atualizar imports de config (`get_redis_client`, `get_supabase_client`).
- [x] Utilizar repositórios específicos em vez de `models.repository`.
- [x] Atualizar testes para usar `InMemoryStore` e fábricas.
- [x] Revisar prompts/documentação de agentes conforme `docs/ARCHITECTURE.md`.
