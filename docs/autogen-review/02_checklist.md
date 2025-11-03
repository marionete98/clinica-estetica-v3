# AutoGen Review - Checklist de Conformidade

Use esta lista para auditar o sistema periodicamente sem introduzir novas features.

Referências de exemplos SK (Gemini/Grok): `docs/autogen-review/05_examples_sk.md`

## Agentes e Ferramentas
- **[AssistantAgent]** Todos os agentes usam `AssistantAgent` com `model_client` via `SKChatCompletionAdapter`? (ver `agents/*.py`)
- **[FunctionTool]** Ferramentas registradas via `FunctionTool` com tipos e docstrings claras? (ex.: `agents/scheduler.py`)
- **[CancelationToken]** `CancellationToken` é sempre criado/ cancelado em `agent.run()`? (intake/faq/scheduler/escalation/supervisor)
- **[Reflexão pós-tool]** `reflect_on_tool_use=True` quando o retorno de tool não é linguagem natural? (rever `faq`/`scheduler`)
- **[Parser central]** `utils.response_parser.parse_messages_from_run_result` é usado consistentemente?

## Assinaturas/Async/Blocking
- **[Async]** Nenhuma chamada síncrona bloqueando o event loop dentro de `async def`? (Ex.: `.execute()` do Supabase)
- **[Supabase Ops]** Uso de `supabase_ops.aselect/ainsert/aupdate/adelete/arun` no `models/repository.py` e `tools/*`?
- **[Thread offload]** Em exceções, usar `await asyncio.to_thread(...)` para evitar bloqueio?

## Configuração/Providers
- **[Providers]** `services/agent_orchestrator._get_llm_config()` padronizado com Semantic Kernel: `gemini` via `GoogleAIChatCompletion`; `xai` via `OpenAIChatCompletion` com `AsyncOpenAI(base_url="https://api.x.ai/v1")`. `openai` apenas opcional/legado – alinhado aos agentes.
- **[Chaves]** `config/settings.py` não valida chaves LLM em import para ambientes de teste/dev (lazy validation)?
- **[Timeouts]** Timeouts coerentes em `settings.response_timeout_seconds` e passados ao `model_client`?

## Timezone/Negócio
- **[TZ]** Datetimes timezone-aware e consistentes com `America/Sao_Paulo`? (agendamento/cancelamento/min advance)
- **[Comercial]** Validação de horário comercial respeitada em todos os fluxos (`scheduler_tools.is_within_business_hours`)?
- **[Políticas]** Regras de cancelamento e limite de remarcação aplicadas antes de executar ação?

## Logging/Telemetria
- **[UTF-8]** Strings/prompt/logs sem caracteres corrompidos ("Cl?nica", "Oli")?
- **[Noise]** Remover ruídos nos logs (`routes/webhooks.py` msgs com tokens/ruas acidentais)?
- **[OTel]** Telemetria sob `enable_telemetry` (gating), sem falhar startup.

## KB/Cache
- **[KB Tool]** `tools/kb_tools_cached.py` retorna estrutura consistente sempre (`{"entries":[],"sources":[]}`)?
- **[Categorias]** Taxonomia de categorias uniforme (ex.: `treatments` vs `Tratamentos`)?
- **[Cache]** FAQ cache com TTL e métricas funcionando, sem vazar chaves?

## Dependências/Build
- **[Autogen]** `autogen-agentchat`, `autogen-core`, `autogen-ext[openai]` versão 0.4.x conforme docs.
- **[pybreaker]** Pinado para versão compatível com Py 3.13 (`1.4.1`).
- **[Semantic Kernel]** `semantic-kernel` presente em `requirements.txt` e validado localmente.
- **[OpenAI client]** `openai` 1.x presente (uso para Grok via `base_url="https://api.x.ai/v1"`).
- **[Deprecados]** `google-generativeai` não utilizado — remover.
- **[OTel beta]** Avaliar riscos das instrumentações beta e manter gating.

## Rotas e Orquestração
- **[DI]** Padrão de DI do orquestrador preferido nas rotas (evitar singleton legado).
- **[Batching]** Acúmulo de mensagens com atraso controlado e locks por conversa (`routes/webhooks.py`).
- **[Rate limit]** Middleware configurado para `"/webhook/"` e cabeçalhos retornados corretamente.
