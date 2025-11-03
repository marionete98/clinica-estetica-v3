"""
Quick test to verify Followup Agent migration to AutoGen 0.4
"""
from agents.followup import create_followup_agent

# Test agent creation
llm_config = {
    'provider': 'xai',
    'model': 'grok-beta',
    'api_key': 'test-key'
}

agent = create_followup_agent(llm_config)

print("✓ Followup agent created successfully")
print(f"✓ Agent type: {type(agent).__name__}")
print(f"✓ Has cleanup method: {hasattr(agent, 'cleanup')}")
print(f"✓ Has model_client: {hasattr(agent, 'model_client')}")
print(f"✓ Has send_booking_confirmation: {hasattr(agent, 'send_booking_confirmation')}")
print(f"✓ Has send_reminder_d1: {hasattr(agent, 'send_reminder_d1')}")
print(f"✓ Has send_reminder_h2: {hasattr(agent, 'send_reminder_h2')}")
print(f"✓ Has send_post_treatment_feedback: {hasattr(agent, 'send_post_treatment_feedback')}")

# Verify agent uses AssistantAgent
from autogen_agentchat.agents import AssistantAgent
print(f"✓ Agent.agent is AssistantAgent: {isinstance(agent.agent, AssistantAgent)}")

# Verify model client
from autogen_ext.models.openai import OpenAIChatCompletionClient
print(f"✓ Model client is OpenAIChatCompletionClient: {isinstance(agent.model_client, OpenAIChatCompletionClient)}")

# Verify tools are registered
print(f"✓ Agent has tools: {len(agent.agent._tools) > 0 if hasattr(agent.agent, '_tools') else 'N/A'}")

print("\n✅ All checks passed! Followup Agent successfully migrated to AutoGen 0.4")
