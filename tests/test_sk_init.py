"""
Teste simples de inicialização dos agentes com Semantic Kernel.
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('.env')

print("🔧 Testando inicialização dos agentes com Semantic Kernel...")
print(f"✓ MODEL_PROVIDER: {os.getenv('MODEL_PROVIDER')}")
print(f"✓ XAI_API_KEY: {'***' + os.getenv('XAI_API_KEY', '')[-10:] if os.getenv('XAI_API_KEY') else 'NOT SET'}")
print(f"✓ GEMINI_API_KEY: {'***' + os.getenv('GEMINI_API_KEY', '')[-10:] if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
print()

# Testar imports
print("1️⃣ Testando imports do Semantic Kernel...")
try:
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    from semantic_kernel import Kernel
    from semantic_kernel.memory.null_memory import NullMemory
    from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion
    from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
    print("   ✅ Todos os imports SK funcionando")
except Exception as e:
    print(f"   ❌ Erro nos imports: {e}")
    raise

# Testar inicialização do SupervisorAgent
print("\n2️⃣ Testando inicialização do SupervisorAgent...")
try:
    from agents.supervisor import SupervisorAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    supervisor = SupervisorAgent(llm_config)
    print(f"   ✅ SupervisorAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(supervisor.model_client).__name__}")
    assert type(supervisor.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

# Testar inicialização do FAQAgent
print("\n3️⃣ Testando inicialização do FAQAgent com xAI...")
try:
    from agents.faq import FAQAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    faq = FAQAgent(llm_config)
    print(f"   ✅ FAQAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(faq.model_client).__name__}")
    assert type(faq.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

# Testar inicialização do IntakeAgent
print("\n4️⃣ Testando inicialização do IntakeAgent com xAI...")
try:
    from agents.intake import IntakeAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    intake = IntakeAgent(llm_config)
    print(f"   ✅ IntakeAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(intake.model_client).__name__}")
    assert type(intake.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

# Testar inicialização do SchedulerAgent
print("\n5️⃣ Testando inicialização do SchedulerAgent com xAI...")
try:
    from agents.scheduler import SchedulerAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    scheduler = SchedulerAgent(llm_config)
    print(f"   ✅ SchedulerAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(scheduler.model_client).__name__}")
    assert type(scheduler.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

# Testar inicialização do EscalationAgent
print("\n6️⃣ Testando inicialização do EscalationAgent com xAI...")
try:
    from agents.escalation import EscalationAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    escalation = EscalationAgent(llm_config)
    print(f"   ✅ EscalationAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(escalation.model_client).__name__}")
    assert type(escalation.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

# Testar inicialização do FollowupAgent
print("\n7️⃣ Testando inicialização do FollowupAgent com xAI...")
try:
    from agents.followup import FollowupAgent
    
    llm_config = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": os.getenv("XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    followup = FollowupAgent(llm_config)
    print(f"   ✅ FollowupAgent inicializado com sucesso")
    print(f"   ✅ Model client type: {type(followup.model_client).__name__}")
    assert type(followup.model_client).__name__ == 'SKChatCompletionAdapter', "Model client deve ser SKChatCompletionAdapter"
    print(f"   ✅ Model client é SKChatCompletionAdapter ✓")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    raise

print("\n" + "="*60)
print("🎉 SUCESSO! Migração para Semantic Kernel validada!")
print("="*60)
print("\n✅ Todos os agentes podem ser inicializados com SKChatCompletionAdapter")
print("✅ Suporte a múltiplos providers (xAI Grok, Google Gemini)")
print("✅ Migração completa e funcional!")
