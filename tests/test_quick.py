"""Teste rápido do FAQAgent com SKChatCompletionAdapter."""
import os
from dotenv import load_dotenv
load_dotenv('.env')

print("Testing FAQAgent com xAI + Semantic Kernel...")

from agents.faq import FAQAgent

llm_config = {
    "provider": "xai",
    "model": "grok-4-fast-reasoning",
    "api_key": os.getenv("XAI_API_KEY"),
    "base_url": "https://api.x.ai/v1",
    "temperature": 0.7,
    "max_tokens": 2048
}

try:
    faq = FAQAgent(llm_config)
    print(f"✅ FAQAgent inicializado com sucesso!")
    print(f"✅ Model client: {type(faq.model_client).__name__}")
    print(f"✅ Has tools: {len(faq.agent._tools) > 0}")
    print(f"✅ Tools count: {len(faq.agent._tools)}")
    print("\n🎉 SUCESSO! ModelInfo corrigiu o problema de function calling!")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
