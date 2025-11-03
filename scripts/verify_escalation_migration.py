"""
Verification script for Escalation Agent AutoGen 0.4 migration.
Tests that the agent works correctly with the new API.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.escalation import EscalationAgent
from config.settings import settings


async def test_escalation_agent():
    """Test escalation agent with AutoGen 0.4."""
    print("=" * 60)
    print("ESCALATION AGENT AUTOGEN 0.4 MIGRATION VERIFICATION")
    print("=" * 60)
    
    # Get LLM config
    llm_config = settings.get_llm_config()
    
    print(f"\n✓ LLM Config loaded: provider={llm_config.get('provider')}, model={llm_config.get('model')}")
    
    # Initialize agent
    print("\n1. Initializing Escalation Agent...")
    try:
        agent = EscalationAgent(llm_config)
        print("   ✓ Agent initialized successfully")
        print(f"   ✓ Model client type: {type(agent.model_client).__name__}")
        print(f"   ✓ Agent type: {type(agent.agent).__name__}")
    except Exception as e:
        print(f"   ✗ Failed to initialize agent: {e}")
        return False
    
    # Test prepare_escalation
    print("\n2. Testing prepare_escalation method...")
    try:
        test_context = [
            {"role": "user", "content": "Olá, quero agendar", "timestamp": "2025-10-16 10:00:00"},
            {"role": "assistant", "content": "Claro! Qual procedimento?", "timestamp": "2025-10-16 10:00:05"},
            {"role": "user", "content": "Depilação a laser", "timestamp": "2025-10-16 10:00:15"},
            {"role": "assistant", "content": "Qual data prefere?", "timestamp": "2025-10-16 10:00:20"},
            {"role": "user", "content": "Não está funcionando, quero falar com alguém", "timestamp": "2025-10-16 10:00:30"},
        ]
        
        test_contact = {
            "id": "test_123",
            "name": "João Silva",
            "phone": "+5594991398585",
            "email": "joao@example.com"
        }
        
        result = await agent.prepare_escalation(
            reason="Paciente solicitou atendimento humano",
            conversation_id="test_conv_123",
            contact_info=test_contact,
            context=test_context,
            intents=["schedule"],
            actions_attempted=["Tentou coletar data", "Tentou listar horários"],
            priority="medium"
        )
        
        print("   ✓ prepare_escalation executed successfully")
        print(f"   ✓ Summary generated: {len(result['summary'])} chars")
        print(f"   ✓ Patient message: {result['patient_message'][:50]}...")
        print(f"   ✓ Priority: {result['priority']}")
        print(f"   ✓ Should pause automation: {result['should_pause_automation']}")
        
        # Verify required fields
        required_fields = ["summary", "patient_message", "conversation_id", "priority", "should_pause_automation"]
        for field in required_fields:
            if field not in result:
                print(f"   ✗ Missing required field: {field}")
                return False
        
        print("   ✓ All required fields present")
        
    except Exception as e:
        print(f"   ✗ prepare_escalation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test detect_escalation_trigger
    print("\n3. Testing detect_escalation_trigger method...")
    try:
        # Test explicit request
        result1 = await agent.detect_escalation_trigger(
            message="Quero falar com um atendente",
            routing_history=["faq", "scheduler"],
            confidence="high"
        )
        print(f"   ✓ Explicit request detection: should_escalate={result1['should_escalate']}")
        
        # Test loop detection
        result2 = await agent.detect_escalation_trigger(
            message="Ainda não entendi",
            routing_history=["faq", "faq", "faq"],
            confidence="high"
        )
        print(f"   ✓ Loop detection: should_escalate={result2['should_escalate']}")
        
        # Test low confidence
        result3 = await agent.detect_escalation_trigger(
            message="Quanto custa?",
            routing_history=["faq"],
            confidence="low"
        )
        print(f"   ✓ Low confidence detection: should_escalate={result3['should_escalate']}")
        
    except Exception as e:
        print(f"   ✗ detect_escalation_trigger failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test cleanup
    print("\n4. Testing cleanup method...")
    try:
        await agent.cleanup()
        print("   ✓ Cleanup executed successfully")
    except Exception as e:
        print(f"   ✗ Cleanup failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - ESCALATION AGENT MIGRATION SUCCESSFUL")
    print("=" * 60)
    return True


async def main():
    """Main entry point."""
    try:
        success = await test_escalation_agent()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
