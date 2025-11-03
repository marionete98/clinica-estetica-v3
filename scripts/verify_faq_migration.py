"""
Verification script for FAQ Agent AutoGen 0.4 migration.
Tests that the FAQ agent works correctly with the new API.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.faq import FAQAgent, create_faq_agent
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_faq_agent_initialization():
    """Test FAQ agent initialization with AutoGen 0.4."""
    logger.info("Testing FAQ agent initialization...")
    
    llm_config = settings.get_llm_config()
    
    try:
        agent = create_faq_agent(llm_config)
        
        # Verify agent has required attributes
        assert hasattr(agent, 'model_client'), "Agent missing model_client"
        assert hasattr(agent, 'agent'), "Agent missing agent"
        assert hasattr(agent, 'llm_config'), "Agent missing llm_config"
        assert hasattr(agent, '_cache'), "Agent missing _cache"
        
        # Verify agent is AssistantAgent
        from autogen_agentchat.agents import AssistantAgent
        assert isinstance(agent.agent, AssistantAgent), "Agent is not AssistantAgent"
        
        logger.info("✅ FAQ agent initialization successful")
        return agent
        
    except Exception as e:
        logger.error(f"❌ FAQ agent initialization failed: {e}")
        raise


async def test_faq_agent_answer_question(agent: FAQAgent):
    """Test FAQ agent answering a question."""
    logger.info("Testing FAQ agent answer_question method...")
    
    try:
        # Test simple question
        response = await agent.answer_question(
            question="Quanto custa depilação a laser?",
            contact_name="João"
        )
        
        # Verify response structure
        assert isinstance(response, dict), "Response is not a dictionary"
        assert "answer" in response, "Response missing 'answer' field"
        assert "confidence" in response, "Response missing 'confidence' field"
        assert "should_escalate" in response, "Response missing 'should_escalate' field"
        
        logger.info(f"✅ FAQ agent answered question successfully")
        logger.info(f"   Answer: {response['answer'][:100]}...")
        logger.info(f"   Confidence: {response['confidence']}")
        logger.info(f"   Should escalate: {response['should_escalate']}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ FAQ agent answer_question failed: {e}")
        raise


async def test_faq_agent_cache(agent: FAQAgent):
    """Test FAQ agent caching functionality."""
    logger.info("Testing FAQ agent cache...")
    
    try:
        # Clear cache first
        agent.clear_cache()
        
        # First call (cache miss)
        question = "Qual o horário de funcionamento?"
        response1 = await agent.answer_question(question)
        assert response1.get("cached") == False, "First call should not be cached"
        
        # Second call (cache hit)
        response2 = await agent.answer_question(question)
        
        # Note: Cache only stores high confidence responses
        if response1.get("confidence") == "high":
            assert response2.get("cached") == True, "Second call should be cached"
            logger.info("✅ FAQ agent cache working correctly")
        else:
            logger.info("✅ FAQ agent cache skipped (low confidence response)")
        
        # Get cache stats
        stats = agent.get_cache_stats()
        logger.info(f"   Cache stats: {stats}")
        
    except Exception as e:
        logger.error(f"❌ FAQ agent cache test failed: {e}")
        raise


async def test_faq_agent_cleanup(agent: FAQAgent):
    """Test FAQ agent cleanup."""
    logger.info("Testing FAQ agent cleanup...")
    
    try:
        await agent.cleanup()
        logger.info("✅ FAQ agent cleanup successful")
        
    except Exception as e:
        logger.error(f"❌ FAQ agent cleanup failed: {e}")
        raise


async def main():
    """Run all verification tests."""
    logger.info("=" * 60)
    logger.info("FAQ Agent AutoGen 0.4 Migration Verification")
    logger.info("=" * 60)
    
    try:
        # Test 1: Initialization
        agent = await test_faq_agent_initialization()
        
        # Test 2: Answer question
        await test_faq_agent_answer_question(agent)
        
        # Test 3: Cache functionality
        await test_faq_agent_cache(agent)
        
        # Test 4: Cleanup
        await test_faq_agent_cleanup(agent)
        
        logger.info("=" * 60)
        logger.info("✅ All FAQ agent migration tests passed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ FAQ agent migration verification failed: {e}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
