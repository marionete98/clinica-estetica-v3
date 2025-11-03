# AutoGen Review - Plano de Correções (Sem Novas Features)

Priorize aplicar estes ajustes em PRs pequenos e focados. Todos os itens abaixo referenciam arquivos do repositório e práticas da documentação oficial do AutoGen 0.4.

## Prioridade Alta (P1)
- **[Padronizar orquestrador para SK (gemini|xai)]**
  - Arquivo: `services/agent_orchestrator.py`, método `_get_llm_config()`
  - Problema: Configuração de LLM não é uniforme entre orquestrador e agentes, e nem sempre usa SK.
  - Ação: Unificar para Semantic Kernel:
    - `gemini`: `GoogleAIChatCompletion` + `SKChatCompletionAdapter`.
    - `xai`: `OpenAIChatCompletion` com `AsyncOpenAI(base_url="https://api.x.ai/v1")` + `SKChatCompletionAdapter`.
    - `openai`: manter apenas como opcional/legado.
  - Impacto: Configuração única e moderna para provedores atuais (Gemini/Grok), menor acoplamento nos agentes.

- **[Migrar agentes legados para SKChatCompletionAdapter]**
  - Arquivos: `agents/*.py`
  - Problema: Alguns agentes ainda usam clientes legados (`OpenAIChatCompletionClient`).
  - Ação: Migrar todos para `SKChatCompletionAdapter` com os conectores SK acima.
  - Impacto: Padronização de camada de modelo, facilidade de tuning (prompt settings), e paridade entre ambientes.

- **[Validação de credenciais apenas em uso (lazy)]**
  - Arquivo: `config/settings.py`
  - Problema: Validação de chaves obrigatórias do provedor LLM acontece ao instanciar `Settings()` (import time), quebrando ambientes de teste sem chaves.
  - Ação: Remover validação rígida de `model_post_init`/`model_validator` e validar apenas em `get_llm_config()` (ou quando `_get_llm_config()` do orquestrador é chamado). Alternativa: manter validação rígida somente quando `ENV=production`.
  - Impacto: Dev/prod estáveis; testes rodam sem segredos.

- **[Supabase síncrono em funções `async`]**
  - Arquivo: `tools/scheduler_tools.py`
  - Locais: buscas de room/equipment via `supabase_client.client...execute()` dentro de `async def`.
  - Ação: Trocar por `await supabase_ops.aselect(...)` ou `await asyncio.to_thread(...)` para evitar bloqueio do event loop.
  - Referência: Prática recomendada de I/O assíncrono.

- **[Strings/logs com ruído e acentuação corrompida]**
  - Arquivos: `routes/webhooks.py` (ex.: "I Waiting...", "oa Collected...", "U1 Conversation...", "14 **Nova mensagem..."), `agents/followup.py`, `main.py` ("Cl?nica").
  - Ação: Corrigir literais para UTF-8 correto e remover tokens acidentais. Não alterar conteúdo semântico.
  - Impacto: Melhora UX, prompt quality e observabilidade.

## Prioridade Média (P2)
- **[Reflexão pós-uso de tool]**
  - Arquivos: `agents/faq.py`, `agents/scheduler.py`
  - Problema: Quando um tool retorna JSON/estruturas, a resposta pode não ser natural.
  - Ação: Considerar `AssistantAgent(..., reflect_on_tool_use=True)` (docs: Agents tutorial) ou manter o parser central com formatação humana, mas padronizar estratégia.

- **[Timezone consistente em agendamentos]**
  - Arquivo: `tools/scheduler_tools.py`
  - Problema: `datetime.now()` ingênuo para regra de antecedência mínima e verificação de horário comercial.
  - Ação: Alinhar com `America/Sao_Paulo` (via `ZoneInfo`) e usar aware datetimes; manter coerência com fonte do Calendar API.

- **[Taxonomia de categorias da KB]**
  - Arquivo: `agents/faq.py`
  - Problema: Uso de `category="treatments"` enquanto comentários usam `"Tratamentos"` (capitalização e idioma divergentes).
  - Ação: Padronizar chaves de categoria (ex.: todas em inglês ou todas em PT-BR) e refletir isso em consultas/filtros.

- **[Dependências SK/LLM]**
  - Arquivo: `requirements.txt`
  - Ação: Adicionar `semantic-kernel` (fixar versão após validação local) e remover `google-generativeai` se não houver uso direto.
  - Impacto: Alinha dependências à abordagem atual (SK + Gemini/Grok), removendo pacotes deprecados.

- **[Rotas e DI]**
  - Arquivo: `routes/api.py`
  - Problema: Endpoint `/chat` usa `orchestrate_agents` (camada de compatibilidade).
  - Ação: Migrar para DI explícito (utilizar `create_orchestrator()` com Depends) para padronizar com webhooks e garantir cleanup por requisição.

## Prioridade Baixa (P3)
- **[Comentários divergindo da versão do AutoGen]**
  - Arquivo: `services/agent_orchestrator.py`
  - Ação: Atualizar comentários para 0.4.x onde consta "0.7.x" (somente documentação interna).

- **[OTel beta pinning]**
  - Arquivo: `requirements.txt`
  - Ação: Manter `enable_telemetry` como gating (já está). Quando versão estável sair, atualizar pins e revisar `config/telemetry.py`.

## Testes Recomendados
- **[Orquestrador SK (gemini/xai)]**
  - Testar `_get_llm_config()` com `MODEL_PROVIDER=gemini` (via `GoogleAIChatCompletion`) e `MODEL_PROVIDER=xai` (via `OpenAIChatCompletion` + `AsyncOpenAI(base_url="https://api.x.ai/v1")`), cobrindo chaves presentes/ausentes.
- **[Supabase assíncrono]**
  - Testar tools do scheduler com `asyncio` ensuring sem bloqueio; mock de `supabase_ops`.
- **[Timezone]**
  - Testes unitários para min advance/horário comercial com `ZoneInfo("America/Sao_Paulo")` e casos de fronteira.
- **[Reflexão e parsing]**
  - Testes para garantir respostas em linguagem natural quando tool retorna JSON (com e sem `reflect_on_tool_use`).
- **[Logs limpíssimos]**
  - Testes de snapshot/logging em pontos onde havia ruído.

## Referências AutoGen
- Agents: `AssistantAgent`, `reflect_on_tool_use`
  - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html
  - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/tools.html
