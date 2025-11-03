"""
Tests for LLM guardrails module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from utils.guardrails import (
    LLMGuardrails,
    GuardrailViolation,
    estimate_tokens,
    check_and_increment_tool_calls,
    check_and_increment_tokens,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch("utils.guardrails.redis_client") as mock:
        client_mock = MagicMock()
        client_mock.incr = AsyncMock(return_value=0)
        client_mock.expire = AsyncMock(return_value=True)
        client_mock.incrby = AsyncMock(return_value=0)
        client_mock.delete = AsyncMock(return_value=1)
        mock.client = client_mock
        mock.get_value = AsyncMock(return_value=None)
        mock.ensure_initialized = AsyncMock()
        mock.set_value = AsyncMock(return_value=True)
        yield mock


def test_guardrails_initialization():
    """Test guardrails initialization with default values."""
    guardrails = LLMGuardrails()

    assert guardrails.max_tool_calls_per_session == 3
    assert guardrails.max_tokens_per_response == 500
    assert guardrails.max_tokens_per_conversation_hour == 10000
    assert guardrails.token_window_seconds == 3600


@pytest.mark.asyncio
async def test_tool_call_limit_within_limit(mock_redis):
    """Test tool call limit check when within limit."""
    mock_redis.get_value.return_value = None

    guardrails = LLMGuardrails()
    result = await guardrails.check_tool_call_limit("conv_123", "session_456")

    assert result is True


@pytest.mark.asyncio
async def test_tool_call_limit_exceeded(mock_redis):
    """Test tool call limit check when limit is exceeded."""
    mock_redis.get_value.return_value = "3"

    guardrails = LLMGuardrails()

    with pytest.raises(GuardrailViolation) as exc_info:
        await guardrails.check_tool_call_limit("conv_123", "session_456")

    assert exc_info.value.limit_type == "tool_calls"
    assert exc_info.value.current_value == 3
    assert exc_info.value.max_value == 3


@pytest.mark.asyncio
async def test_increment_tool_call_count(mock_redis):
    """Test incrementing tool call counter."""
    mock_redis.client.incr.return_value = 1

    guardrails = LLMGuardrails()
    count = await guardrails.increment_tool_call_count("conv_123", "session_456")

    assert count == 1
    mock_redis.client.incr.assert_awaited_once()
    mock_redis.client.expire.assert_awaited_once()


def test_response_token_limit_within_limit():
    """Test response token limit when within limit."""
    guardrails = LLMGuardrails()
    result = guardrails.check_response_token_limit(400)

    assert result is True


def test_response_token_limit_exceeded():
    """Test response token limit when exceeded."""
    guardrails = LLMGuardrails()

    with pytest.raises(GuardrailViolation) as exc_info:
        guardrails.check_response_token_limit(600)

    assert exc_info.value.limit_type == "response_tokens"
    assert exc_info.value.current_value == 600
    assert exc_info.value.max_value == 500


@pytest.mark.asyncio
async def test_conversation_token_limit_within_limit(mock_redis):
    """Test conversation token limit when within limit."""
    mock_redis.get_value.return_value = None

    guardrails = LLMGuardrails()
    result = await guardrails.check_conversation_token_limit("conv_123", 1000)

    assert result is True


@pytest.mark.asyncio
async def test_conversation_token_limit_exceeded(mock_redis):
    """Test conversation token limit when exceeded."""
    mock_redis.get_value.return_value = "9500"

    guardrails = LLMGuardrails()

    with pytest.raises(GuardrailViolation) as exc_info:
        await guardrails.check_conversation_token_limit("conv_123", 1000)

    assert exc_info.value.limit_type == "conversation_tokens"
    assert exc_info.value.current_value == 10500
    assert exc_info.value.max_value == 10000


@pytest.mark.asyncio
async def test_increment_conversation_tokens(mock_redis):
    """Test incrementing conversation token counter."""
    mock_redis.client.incrby.return_value = 1000

    guardrails = LLMGuardrails()
    count = await guardrails.increment_conversation_tokens("conv_123", 1000)

    assert count == 1000
    mock_redis.client.incrby.assert_awaited_once()
    await_args = mock_redis.client.incrby.await_args
    assert await_args.args[1] == 1000  # Second argument should be the token count


def test_sanitize_user_message():
    """Test user message sanitization."""
    guardrails = LLMGuardrails()

    message = "Hello, I want to book an appointment"
    sanitized = guardrails.sanitize_user_message(message)

    assert sanitized == "User says: Hello, I want to book an appointment"
    assert sanitized.startswith("User says: ")


def test_sanitize_user_message_with_whitespace():
    """Test user message sanitization with extra whitespace."""
    guardrails = LLMGuardrails()

    message = "  Hello, I want to book an appointment  "
    sanitized = guardrails.sanitize_user_message(message)

    assert sanitized == "User says: Hello, I want to book an appointment"


@pytest.mark.asyncio
async def test_get_tool_call_count(mock_redis):
    """Test getting current tool call count."""
    mock_redis.get_value.return_value = "2"

    guardrails = LLMGuardrails()
    count = await guardrails.get_tool_call_count("conv_123", "session_456")

    assert count == 2


@pytest.mark.asyncio
async def test_get_tool_call_count_none(mock_redis):
    """Test getting tool call count when none exists."""
    mock_redis.get_value.return_value = None

    guardrails = LLMGuardrails()
    count = await guardrails.get_tool_call_count("conv_123", "session_456")

    assert count == 0


@pytest.mark.asyncio
async def test_get_conversation_token_count(mock_redis):
    """Test getting current conversation token count."""
    mock_redis.get_value.return_value = "5000"

    guardrails = LLMGuardrails()
    count = await guardrails.get_conversation_token_count("conv_123")

    assert count == 5000


@pytest.mark.asyncio
async def test_reset_session_limits(mock_redis):
    """Test resetting session limits."""
    guardrails = LLMGuardrails()
    await guardrails.reset_session_limits("conv_123", "session_456")

    mock_redis.client.delete.assert_awaited_once()
    await_args = mock_redis.client.delete.await_args
    assert await_args.args[0] == "guardrail:toolcalls:conv_123:session_456"


def test_estimate_tokens():
    """Test token estimation."""
    text = "This is a test message"
    tokens = estimate_tokens(text)

    # Should be roughly len(text) / 4
    expected = len(text) // 4
    assert tokens == expected


def test_estimate_tokens_minimum():
    """Test token estimation returns at least 1."""
    text = "Hi"
    tokens = estimate_tokens(text)

    assert tokens >= 1


@pytest.mark.asyncio
async def test_check_and_increment_tool_calls(mock_redis):
    """Test helper function for checking and incrementing tool calls."""
    mock_redis.get_value.return_value = None
    mock_redis.client.incr.return_value = 1

    guardrails = LLMGuardrails()
    count = await check_and_increment_tool_calls("conv_123", "session_456", guardrails)

    assert count == 1


@pytest.mark.asyncio
async def test_check_and_increment_tokens(mock_redis):
    """Test helper function for checking and incrementing tokens."""
    mock_redis.get_value.return_value = None
    mock_redis.client.incrby.return_value = 1000

    guardrails = LLMGuardrails()
    count = await check_and_increment_tokens("conv_123", 1000, guardrails)

    assert count == 1000


def test_guardrail_violation_exception():
    """Test GuardrailViolation exception attributes."""
    exc = GuardrailViolation(
        message="Test violation",
        limit_type="test_limit",
        current_value=100,
        max_value=50,
    )

    assert exc.message == "Test violation"
    assert exc.limit_type == "test_limit"
    assert exc.current_value == 100
    assert exc.max_value == 50
    assert str(exc) == "Test violation"

