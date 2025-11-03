# AutoGen Review - Matriz de Versões (Python 3.13)

Esta matriz consolida versões recomendadas e compatíveis para o stack atual, alinhada ao uso do AutoGen 0.4 e às bibliotecas já presentes no projeto. Sempre manter os 3 pacotes do AutoGen no mesmo patch (0.4.x) para evitar quebras.

## AutoGen Stack
- **autogen-agentchat:** 0.4.0 (ou última patch 0.4.x quando disponível)
- **autogen-core:** 0.4.0 (sincronizado com agentchat)
- **autogen-ext[openai]:** 0.4.0 (sincronizado com agentchat)

Observação: manter os 3 pacotes alinhados no mesmo patch (ex.: 0.4.0/0.4.0/0.4.0). Se atualizar, atualizar os três juntos.

## LLM Clients
- **semantic-kernel:** latest estável; recomendado para integrar Gemini (GoogleAI) e Grok (xAI via OpenAI-compatível) com `SKChatCompletionAdapter`.
- **openai:** 1.105.0 (usado para Grok via `base_url="https://api.x.ai/v1"`; manter na linha 1.x).

## Web Framework / Server
- **fastapi[standard]:** 0.119.0
- **uvicorn[standard]:** 0.37.0
- **python-multipart:** 0.0.18

## Data, DB e Cache
- **supabase:** 2.22.0
- **redis:** 6.4.0
- **psycopg2-binary:** 2.9.11
- **httpx:** 0.28.1
- **tenacity:** 9.1.2
- **pybreaker:** 1.4.1 (compatível Py 3.13)

## Validação e Configs
- **pydantic:** 2.12.2
- **pydantic-settings:** 2.11.0
- **python-dateutil:** 2.9.0.post0
- **typing-extensions:** 4.15.0

## Observabilidade (gated por enable_telemetry)
- **opentelemetry-sdk:** 1.27.0
- **opentelemetry-exporter-otlp:** 1.27.0
- **opentelemetry-instrumentation-fastapi:** 0.47b0 (beta)
- **opentelemetry-instrumentation-httpx:** 0.47b0 (beta)

Nota: manter apenas com `enable_telemetry=true`. Avaliar atualização para versões estáveis quando disponíveis.

## Scheduling e Utilitários
- **apscheduler:** 3.10.4
- **pytz:** 2024.2 (usar ZoneInfo preferencialmente em novo código)
- **python-dotenv:** 1.0.1
- **PyJWT:** 2.10.1
- **structlog:** 25.4.0
- **orjson:** 3.10.13
- **PyYAML:** 6.0.2
- **rich:** 13.9.4
- **psutil:** 6.1.0

## Testes e Qualidade
- **pytest:** 8.3.4
- **pytest-asyncio:** 0.24.0
- **pytest-cov:** 6.0.0
- **responses:** 0.25.3
- **black:** 24.10.0
- **flake8:** 7.1.1
- **mypy:** 1.13.0
- **isort:** 5.13.2

## Diretrizes de Pinagem
- **AutoGen (0.4.x):** manter agentchat/core/ext no mesmo patch.
- **OpenAI 1.x:** manter dentro da linha 1.x estável.
- **Remover pacotes deprecados não usados:** `google-generativeai` se não houver chamada direta.
- **Compatibilidade Py 3.13:** já validada para `psycopg2-binary` (wheel cp313), `pybreaker 1.4.1`, `redis 6.4.0`.

## Próximos Passos
- Adicionar `semantic-kernel` ao `requirements.txt` (fixar versão após validação local).
- Remover `google-generativeai` do `requirements.txt` se não houver uso direto.
- Avaliar atualizar AutoGen para o último patch `0.4.x` (mantendo trio sincronizado).
- Manter OTel instrumentation sob flag; atualizar para estável quando houver.
