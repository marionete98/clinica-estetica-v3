## Plano de Refatoração do Orquestrador (Sprint 3 - Fase 3.1)

Objetivo: reduzir o acoplamento do `AgentOrchestrator`, distribuindo responsabilidades em módulos coesos e reutilizáveis, mantendo compatibilidade com a DI do FastAPI (`create_orchestrator` e `orchestrator_lifespan`).

### Estrutura Proposta

```
services/orchestrator/
├─ __init__.py                # expõe AgentOrchestrator e helpers principais
├─ orchestrator.py            # classe AgentOrchestrator delegando para componentes internos
├─ agent_pool.py              # criação e limpeza dos agentes via AgentFactory
├─ context_service.py         # leitura/escrita de contexto no Redis
├─ session_service.py         # leitura/escrita de sessões (Supabase)
├─ routing_pipeline.py        # fluxo principal de orquestração (supervisor + agentes)
└─ response_parsers.py        # formatações auxiliares (ex.: markers do scheduler)
```

### Benefícios Esperados

- Separação clara de responsabilidades: cada módulo foca em um domínio específico.
- Facilidade para testes unitários isolados (contexto, sessão, pipeline).
- Menos riscos de regressões ao alterar um fluxo específico.
- Preparação para futuras otimizações (ex.: observabilidade, métricas unificadas).

### Estratégia de Implantação

1. **Criar nova estrutura** mantendo o conteúdo atual copiado e dividido gradualmente.
2. **Atualizar `services/agent_orchestrator.py`** para tornar-se um _shim_ que apenas importa o novo módulo, garantindo compatibilidade com os pontos de entrada existentes (`main.py`, `routes/api.py`, scripts).
3. **Adicionar testes focados** (mínimo: carga de contexto e pipeline de roteamento simulados) para cobrir o novo layout.
4. **Remover código morto** e comentários duplicados após migração.

### Próximos Passos

- Implementar módulos `agent_pool`, `context_service`, `session_service`, `response_parsers`.
- Regravar o fluxo principal em `routing_pipeline` e adaptar o `AgentOrchestrator` para delegar às funções desses módulos.
- Ajustar importações em `main.py`, `routes`, scripts e testes para apontar para `services.orchestrator`.

