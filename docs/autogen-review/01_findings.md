# AutoGen Review - Findings

- **Escopo:** Revisão técnica do uso do AutoGen 0.4 (AgentChat/Core/Ext), ferramentas (`FunctionTool`), clientes de modelo e integração com orquestração e rotas.
- **Docs oficiais:** https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/index.html
- **Exemplos SK (Gemini/Grok):** `docs/autogen-review/05_examples_sk.md`

## Conformidade com AutoGen 0.4
- **[RECOMENDADO] AssistantAgent + model_client:** Padronizar `SKChatCompletionAdapter` com `GoogleAIChatCompletion` (Gemini) e `OpenAIChatCompletion` com `AsyncOpenAI(base_url="https://api.x.ai/v1")` para Grok; migrar clientes legados (`OpenAIChatCompletionClient`) gradualmente.
- **[OK] Tools (FunctionTool):** Ferramentas expostas via `autogen_core.tools.FunctionTool` com anotações de tipos e docstrings descritivas (ex.: `agents/scheduler.py`).
- **[OK] CancelationToken:** Criação/limpeza de `CancellationToken` nas chamadas `agent.run(...)` (padrão recomendado).
- **[PARCIAL] Reflexão pós-tools:** `reflect_on_tool_use=True` apenas no `intake`. FAQ/Scheduler podem se beneficiar quando resposta do tool não é linguagem natural (ver seção Correções 5.).

## Pontos de Correção (prioridade em parênteses)
- **1) Padronizar orquestrador para SK (gemini|xai) (P1)**
  - Arquivo: `services/agent_orchestrator.py` (`_get_llm_config()`)
  - Problema: Configuração de LLM não é uniforme entre orquestrador e agentes, e nem sempre usa SK.
  - Correção: Recomendar `_get_llm_config()` para retornar configuração baseada em Semantic Kernel: para `gemini`, `GoogleAIChatCompletion`; para `xai`, `OpenAIChatCompletion` com `AsyncOpenAI(base_url="https://api.x.ai/v1")`. Suporte `openai` apenas como opcional/legado.

- **2) Validação de credenciais no import (P1)**
  - Arquivo: `config/settings.py`
  - Problema: `Settings()` valida chaves obrigatórias (via `model_post_init`/`model_validator`) no import, quebrando testes/execuções que não usam LLM.
  - Correção: Mover a validação para uso (ex.: `_get_llm_config()`/`settings.get_llm_config()`), ou condicionar validação estrita a `ENV=production`.

- **3) Chamadas síncronas a Supabase em funções assíncronas (P1)**
  - Arquivo: `tools/scheduler_tools.py`
  - Problemas:
    - Busca de `rooms/equipment` via `supabase_client.client` com `.execute()` síncrono dentro de `async def`.
  - Correção: Usar `supabase_ops.aselect(...)` ou `await asyncio.to_thread(...)` para não bloquear o event loop.

- **4) Strings/prompt com acentuação corrompida (P1)**
  - Arquivos: `agents/followup.py` (várias linhas), `main.py` e outros com "Cl?nica" etc.
  - Impacto: Pior desempenho do LLM e UX (mensagens ao paciente).
  - Correção: Regravar literais com UTF-8 correto (sem alterar semântica/conteúdo).

- **5) Reflexão pós-tool onde resposta de tool não é natural (P2)**
  - Arquivos: `agents/faq.py`, `agents/scheduler.py`
  - Problema: Quando ferramentas retornam JSON/estruturas, respostas podem sair "frias". AutoGen recomenda `reflect_on_tool_use=True` para resumir em linguagem natural.
  - Correção: Ativar `reflect_on_tool_use=True` onde apropriado. Alternativa já usada: `parse_messages_from_run_result` + formatação; manter consistente.

- **6) Logs e mensagens com tokens/ruído (P1)**
  - Arquivo: `routes/webhooks.py`
  - Exemplos: `logger.info("I Waiting ...")`, `"oa Collected ..."`, `"U1 Conversation ..."`, `"14 **Nova mensagem ..."`.
  - Correção: Limpar strings/logs acidentais.

- **7) Categoria KB inconsistente (P2)**
  - Arquivo: `agents/faq.py`
  - Problema: Usa `category="treatments"` enquanto comentários e outros pontos sugerem capitalizações diferentes (`Tratamentos`).
  - Correção: Uniformizar taxonomia de categorias (semântica igual, apenas padronizar chave).

- **8) Horário comercial/min advance com datetimes ingênuos (P2)**
  - Arquivo: `tools/scheduler_tools.py`
  - Problema: Usa `datetime.now()` ingênuo; nós já corrigimos timezone em `reschedule_tools.py`.
  - Correção: Consistir timezone-aware (`ZoneInfo("America/Sao_Paulo")`) para min advance; alinhar com fonte do Calendar API.

- **9) Dependências e deprecados/beta (P2)**
  - Arquivo: `requirements.txt`
  - Itens:
    - Adicionar `semantic-kernel` para integrações via SK (`SKChatCompletionAdapter`, `GoogleAIChatCompletion`, `OpenAIChatCompletion` com `base_url` xAI).
    - Remover `google-generativeai==0.8.5` se não houver uso direto (pacote deprecado).
    - `opentelemetry-instrumentation-...==0.47b0` (beta) — ok se gating por `enable_telemetry` (já está); documentar risco.
  - Correção: Incluir `semantic-kernel` e remover pacotes deprecados; avaliar pin estável para OTel quando disponível.

- **10) Divergência de versão AutoGen em comentários (P3)**
  - Arquivo: `services/agent_orchestrator.py`
  - Problema: Comentário menciona "AutoGen 0.7.x" mas `requirements.txt` usa 0.4.0.
  - Correção: Ajustar comentário (não funcional). Opcional.

## Referências (AutoGen)
- Agents: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html
- Tools (FunctionTool): https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/tools.html
- API de Agentes (refs): https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.agents.html
