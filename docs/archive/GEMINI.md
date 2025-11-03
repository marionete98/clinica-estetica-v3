# Guia Gemini para Clínica Luana Multi-Agent System

Este documento serve como um guia de referência rápida para o projeto "Clínica Luana Multi-Agent System", fornecendo um resumo de sua arquitetura, como configurar e executar o projeto localmente, e as convenções de desenvolvimento.

## Visão Geral do Projeto

O "Clínica Luana Multi-Agent System" é um sistema de atendimento automatizado multi-agente para WhatsApp, projetado para a Clínica Luana Carla Dermo Clinic. Ele gerencia agendamentos de procedimentos estéticos, responde a perguntas frequentes (FAQ), lida com remarcações e cancelamentos, e escala para atendimento humano quando necessário.

**Principais Tecnologias:**
*   **Gateway:** FastAPI
*   **Orquestração:** AutoGen 0.4 AgentChat (modular)
*   **LLMs:** Google Gemini 2.5 Flash (padrão para FAQ e Scheduler), xAI Grok-4-Reasoning (opcional para raciocínio complexo). Otimização de tokens com prompts de sistema em inglês e respostas em português.
*   **Banco de Dados:** Supabase (Postgres)
*   **Cache:** Redis Cloud (contexto de conversa + cache de base de conhecimento)
*   **Comunicação:** Chatwoot (entrada/saída WhatsApp)
*   **Deploy:** Railway

**Arquitetura:**
O sistema é baseado em uma arquitetura modular com agentes AutoGen, utilizando `async/await` para operações assíncronas, uma arquitetura `AssistantAgent` moderna e registro direto de ferramentas. Inclui mecanismos de limpeza de recursos e foi migrado para AutoGen 0.4 em Outubro de 2025.

**Funcionalidades Chave:**
*   Agendamento, remarcação e cancelamento de procedimentos.
*   Respostas a FAQs com sistema de cache inteligente.
*   Escalação para atendimento humano.
*   Melhorias na integração com Chatwoot: deduplicação de mensagens, agrupamento de mensagens, suporte a intervenção humana e filtro de mensagens privadas.
*   Cache de base de conhecimento ultra-rápido com Redis e sincronização automática.
*   Otimização de prompts de agentes para redução de custos.

## Configuração e Execução Local

### Pré-requisitos

*   Python 3.11+
*   Redis (local ou Redis Cloud)
*   Conta Supabase
*   Conta xAI ou Google AI
*   Conta Chatwoot

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <repository-url>
    cd clinica-luana-agent-system
    ```
2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    # No Linux/Mac:
    source venv/bin/activate
    # No Windows:
    venv\Scripts\activate
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure as variáveis de ambiente:**
    ```bash
    cp .env.example .env
    # Edite o arquivo .env com suas credenciais e configurações
    ```
    Consulte `.env.example` para a lista completa de variáveis.

### Execução

1.  **Inicie a aplicação:**
    ```bash
    uvicorn main:app --reload
    ```
2.  **(Opcional) Popule o banco de dados:**
    ```bash
    python scripts/seed_data_v2.py
    ```
3.  **Acesse a documentação da API:**
    ```
    http://localhost:8000/docs
    ```

## Testes

O projeto possui uma suíte de testes abrangente.

### Executando Testes

*   **Todos os testes:**
    ```bash
    pytest tests/ -v
    ```
*   **Suítes de testes específicas:**
    ```bash
    pytest tests/test_e2e.py -v                          # Conversas E2E
    pytest tests/test_performance.py -v                  # Validação de performance
    pytest tests/test_error_scenarios.py -v              # Tratamento de erros
    pytest tests/test_chatwoot_improvements.py -v        # Melhorias no Chatwoot
    pytest tests/test_faq_cache.py -v                    # Sistema de cache de FAQ
    pytest tests/test_tools.py -v                        # Funções de ferramentas
    pytest tests/test_kb_cache.py -v                     # Funcionalidade de cache da KB
    ```
*   **Com cobertura de código:**
    ```bash
    pytest --cov=. tests/
    ```
*   **Testes de carga (Locust):**
    ```bash
    locust -f tests/load_tests.py
    ```

## Convenções de Desenvolvimento

### Acesso à Configuração

Utilize o módulo `config.settings` para acessar as variáveis de ambiente e configurações. É recomendado usar o acesso por propriedade em minúsculas:

```python
from config.settings import settings

provider = settings.model_provider  # 'xai' ou 'gemini'
env = settings.env                  # 'development', 'staging', 'production'

if settings.is_production:
    # Lógica específica de produção
    pass
```

### Tratamento de Erros e Resiliência

O sistema implementa um tratamento de erros robusto com retry logic, graceful degradation, validação de entrada e guardrails.

*   **Retry Logic:** `utils/error_handlers.py` para retentativas automáticas com backoff exponencial.
*   **Graceful Degradation:** `utils/graceful_degradation.py` para manter a operação mesmo com serviços indisponíveis.
*   **Input Validation:** `utils/validators.py` para validação e sanitização de entradas.
*   **Guardrails:** `utils/guardrails.py` para proteção contra uso excessivo de recursos (rate limiting, limites de tokens, limites de chamadas de ferramentas).

### Conexões de Clientes Externos

O sistema utiliza instâncias singleton para clientes de serviços externos (Supabase, Redis, Chatwoot). O padrão correto para importação e uso é:

```python
# Supabase
from config.supabase_client import supabase_client
supabase = supabase_client.client

# Redis
from config.redis_client import redis_client

# Chatwoot
from config.chatwoot_client import chatwoot_client
```

**Importante:** Evite o padrão legado `from config.supabase_client import get_supabase_client` pois ele causará um `ImportError`.

## Monitoramento

*   **Health check:** `GET /health`
*   **Métricas:** `GET /metrics`
*   **Dashboard:** `GET /dashboard`
*   **Métricas de Cache da KB:** `GET /metrics/kb-cache`

## Scripts Úteis

*   **População do Banco de Dados:** `python scripts/seed_data_v2.py`
*   **Validação da Infraestrutura de Cache:** `python scripts/test_simple_cache.py`
*   **Inspeção do Redis:** `python scripts/inspect_redis.py`

Para mais detalhes sobre todos os scripts disponíveis, consulte `scripts/README.md`.
