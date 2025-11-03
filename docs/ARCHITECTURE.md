# Arquitetura do Sistema Multi-Agente

## Visão Geral
O sistema é composto por uma API FastAPI que orquestra múltiplos agentes AutoGen responsáveis por intake, FAQ, agendamento e escalonamento. A camada de orquestração coordena memória, roteamento e execução dos agentes com dependências injectáveis via factories.

## Camadas

### 1. API Layer (`routes/`)
- Webhooks HTTP (Chatwoot e integrações futuras)
- Endpoints REST auxiliares
- Dependency Injection através de `Depends`
- Factory `create_orchestrator()`/`orchestrator_lifespan()` fornece instâncias efêmeras

### 2. Orchestration Layer (`services/orchestration/`)
- `orchestrator.py`: coordenação high-level
- `conversation_manager.py`: gerenciamento de contexto/memória
- `routing_engine.py`: roteamento orientado por intents
- `agent_coordinator.py`: execução com retries e observabilidade

### 3. Agent Layer (`agents/`)
- Supervisor, Intake, FAQ, Scheduler, Escalation, Followup
- Factory centralizada em `agents/agent_factory.py`
- Prompts e ferramentas modularizados por agente

### 4. Data Layer (`models/repositories/`)
- `contact_repository.py`: contatos com cache e Supabase
- `appointment_repository.py`: ciclo de vida de agendamentos
- `session_repository.py`: estado de conversas
- `template_repository.py`: templates dinâmicos
- `knowledge_base_repository.py`: busca de conteúdo e templates
- `services.py`: catálogo de serviços clínicos

### 5. Infrastructure Layer
- Memory Store (Redis/InMemory) em `services/memory`
- LLM Client Factory (`agents/model_client_factory.py`)
- Configurações centralizadas (`config/`)

## Padrões de Design
- Factory Pattern (AgentFactory, ModelClientFactory, repositórios DI)
- Repository Pattern (repositórios específicos por domínio)
- Strategy Pattern (implementações de `MemoryStore`)
- Dependency Injection (FastAPI Depends + container de serviços)

## Fluxo de Dados
1. Webhook recebe mensagem -> `AgentOrchestrator` carrega contexto via `ConversationManager`.
2. `RoutingEngine` consulta Supervisor para classificar intenção.
3. `AgentCoordinator` executa agente alvo com retries.
4. Resposta e metadados persistidos via repositórios dedicados.

## Observabilidade
- Logs estruturados com `structlog`
- Métricas centralizadas em `services/metrics.py`
- Circuit breakers e retries configuráveis em `utils/circuit_breakers.py` e `utils/retry.py`
