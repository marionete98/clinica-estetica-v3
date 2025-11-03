# AutoGen + Semantic Kernel: Exemplos (Gemini e Grok)

Estes exemplos mostram como integrar Google Gemini e xAI Grok com AutoGen 0.4 usando o `SKChatCompletionAdapter` do pacote `autogen-ext`, evitando OpenAI como provedor direto.

Requisitos mínimos:
- `autogen-agentchat==0.4.x`, `autogen-core==0.4.x`, `autogen-ext[openai]==0.4.x`
- `semantic-kernel` (instalar a versão estável)
- `openai==1.x` (apenas para usar Grok via `base_url` compatível com OpenAI)

## 1) Gemini (GoogleAI) via Semantic Kernel

```python
import os
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import UserMessage
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion

async def main() -> None:
    # Configure via env vars
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    gemini_key = os.environ["GOOGLE_AI_API_KEY"]

    sk_client = GoogleAIChatCompletion(
        gemini_model_id=gemini_model,
        api_key=gemini_key,
    )

    model_client = SKChatCompletionAdapter(
        sk_client,
        kernel=Kernel(memory=NullMemory()),
    )

    # Chamada direta
    result = await model_client.create(
        messages=[UserMessage(content="Resumo curto sobre peelings químicos.", source="user")]
    )
    print("Gemini result:", result)

    # Uso com AssistantAgent
    assistant = AssistantAgent("gemini_assistant", model_client=model_client)
    resp = await assistant.run(task="Liste 3 benefícios dos retinoides para pele.")
    print("Agent response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
```

## 2) Grok (xAI) via Semantic Kernel + OpenAI-compatível

```python
import os
import asyncio
from openai import AsyncOpenAI

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import UserMessage
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)

async def main() -> None:
    xai_model = os.getenv("XAI_MODEL", "grok-2")
    xai_key = os.environ["XAI_API_KEY"]

    # Cliente OpenAI-compatível apontando para xAI
    async_client = AsyncOpenAI(
        api_key=xai_key,
        base_url="https://api.x.ai/v1",
    )

    sk_client = OpenAIChatCompletion(
        ai_model_id=xai_model,
        async_client=async_client,
    )

    model_client = SKChatCompletionAdapter(
        sk_client,
        kernel=Kernel(memory=NullMemory()),
    )

    # Chamada direta
    result = await model_client.create(
        messages=[UserMessage(content="Dê 3 casos de uso de IA em dermatologia.", source="user")]
    )
    print("Grok result:", result)

    # Uso com AssistantAgent
    assistant = AssistantAgent("grok_assistant", model_client=model_client)
    resp = await assistant.run(task="Explique peelings químicos em linguagem para pacientes.")
    print("Agent response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
```

Notas:
- Ajuste `GEMINI_MODEL`/`XAI_MODEL` conforme o que está habilitado na sua conta.
- Para tunar temperatura/tokens, use as `PromptExecutionSettings` específicas de cada conector SK (opcional).
- Para streaming, prefira `await model_client.create_stream(...)` e itere sobre o gerador assíncrono.
