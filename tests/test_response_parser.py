"""
Unit tests for centralized response parser.

Tests cover all response formats from AutoGen 0.7.x agents:
- TaskResult.messages (list of message objects)
- Response objects with chat_message
- Response objects with content
- Direct strings
- Edge cases (None, empty, unexpected types)
"""

import pytest
from utils.response_parser import safe_parse_response, parse_messages_from_run_result


class TestSafeParseResponse:
    """Test suite for safe_parse_response function."""
    
    def test_parse_message_list_with_content(self):
        """Test parsing list of messages with content attribute (most common)."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [
            MockMessage("First message"),
            MockMessage("Second message"),
            MockMessage("Final response")
        ]
        
        result = safe_parse_response(messages, "test_agent")
        assert result == "Final response"
    
    def test_parse_single_message_in_list(self):
        """Test parsing single message in list."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage("Single response")]
        result = safe_parse_response(messages, "test_agent")
        assert result == "Single response"
    
    def test_parse_message_with_whitespace(self):
        """Test that whitespace is stripped."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage("  Response with spaces  \n")]
        result = safe_parse_response(messages, "test_agent")
        assert result == "Response with spaces"
    
    def test_parse_chat_message_attribute(self):
        """Test parsing response with chat_message attribute."""
        class MockChatMessage:
            def __init__(self, content):
                self.content = content
        
        class MockResponse:
            def __init__(self, content):
                self.chat_message = MockChatMessage(content)
        
        response = MockResponse("Chat message response")
        result = safe_parse_response(response, "test_agent")
        assert result == "Chat message response"
    
    def test_parse_content_attribute(self):
        """Test parsing response with direct content attribute."""
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        response = MockResponse("Direct content response")
        result = safe_parse_response(response, "test_agent")
        assert result == "Direct content response"
    
    def test_parse_direct_string(self):
        """Test parsing direct string response."""
        response = "Direct string response"
        result = safe_parse_response(response, "test_agent")
        assert result == "Direct string response"
    
    def test_parse_none_raises_error(self):
        """Test that None response raises ValueError."""
        with pytest.raises(ValueError, match="Response is None"):
            safe_parse_response(None, "test_agent")
    
    def test_parse_none_with_fallback(self):
        """Test that None response uses fallback if provided."""
        result = safe_parse_response(None, "test_agent", fallback="Fallback message")
        assert result == "Fallback message"
    
    def test_parse_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Response string is empty"):
            safe_parse_response("", "test_agent")
    
    def test_parse_empty_string_with_fallback(self):
        """Test that empty string uses fallback if provided."""
        result = safe_parse_response("", "test_agent", fallback="Fallback message")
        assert result == "Fallback message"
    
    def test_parse_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Response string is empty"):
            safe_parse_response("   \n\t  ", "test_agent")
    
    def test_parse_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Response is empty list"):
            safe_parse_response([], "test_agent")
    
    def test_parse_empty_list_with_fallback(self):
        """Test that empty list uses fallback if provided."""
        result = safe_parse_response([], "test_agent", fallback="Fallback message")
        assert result == "Fallback message"
    
    def test_parse_message_with_empty_content(self):
        """Test that message with empty content raises ValueError."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage("")]
        with pytest.raises(ValueError, match="Message content is empty"):
            safe_parse_response(messages, "test_agent")
    
    def test_parse_message_with_empty_content_fallback(self):
        """Test that message with empty content uses fallback."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage("")]
        result = safe_parse_response(messages, "test_agent", fallback="Fallback")
        assert result == "Fallback"
    
    def test_parse_non_string_content_converts(self):
        """Test that non-string content is converted to string."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage(12345)]
        result = safe_parse_response(messages, "test_agent")
        assert result == "12345"
    
    def test_parse_dict_content_converts(self):
        """Test that dict content is converted to string."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage({"key": "value"})]
        result = safe_parse_response(messages, "test_agent")
        assert "key" in result and "value" in result
    
    def test_parse_message_without_content_attribute(self):
        """Test parsing message object without content attribute."""
        class MockMessage:
            def __str__(self):
                return "String representation"
        
        messages = [MockMessage()]
        result = safe_parse_response(messages, "test_agent")
        assert result == "String representation"
    
    def test_parse_complex_object_fallback(self):
        """Test that complex unparseable object uses fallback."""
        class ComplexObject:
            pass
        
        obj = ComplexObject()
        result = safe_parse_response(obj, "test_agent", fallback="Fallback")
        # Should either parse to string or use fallback
        assert isinstance(result, str)
    
    def test_agent_name_in_error_message(self):
        """Test that agent name appears in error messages."""
        with pytest.raises(ValueError, match="custom_agent"):
            safe_parse_response(None, "custom_agent")
    
    def test_parse_nested_message_structure(self):
        """Test parsing nested message structure."""
        class MockContent:
            def __init__(self, text):
                self.text = text
            
            def __str__(self):
                return self.text
        
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage(MockContent("Nested content"))]
        result = safe_parse_response(messages, "test_agent")
        assert result == "Nested content"


class TestParseMessagesFromRunResult:
    """Test suite for parse_messages_from_run_result convenience function."""
    
    def test_parse_run_result_with_messages(self):
        """Test parsing TaskResult with messages attribute."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        class MockRunResult:
            def __init__(self, messages):
                self.messages = messages
        
        run_result = MockRunResult([MockMessage("Result from run")])
        result = parse_messages_from_run_result(run_result, "test_agent")
        assert result == "Result from run"
    
    def test_parse_run_result_without_messages(self):
        """Test parsing result without messages attribute (fallback)."""
        class MockRunResult:
            def __init__(self, content):
                self.content = content
        
        run_result = MockRunResult("Direct content")
        result = parse_messages_from_run_result(run_result, "test_agent")
        assert result == "Direct content"
    
    def test_parse_run_result_none_raises(self):
        """Test that None run_result raises ValueError."""
        with pytest.raises(ValueError):
            parse_messages_from_run_result(None, "test_agent")


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_parse_unicode_content(self):
        """Test parsing Unicode content."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        messages = [MockMessage("Olá! Como posso ajudar? 😊")]
        result = safe_parse_response(messages, "test_agent")
        assert result == "Olá! Como posso ajudar? 😊"
    
    def test_parse_multiline_content(self):
        """Test parsing multiline content."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        multiline = """Line 1
Line 2
Line 3"""
        messages = [MockMessage(multiline)]
        result = safe_parse_response(messages, "test_agent")
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    def test_parse_very_long_content(self):
        """Test parsing very long content."""
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        long_content = "A" * 10000
        messages = [MockMessage(long_content)]
        result = safe_parse_response(messages, "test_agent")
        assert len(result) == 10000
        assert result == long_content
    
    def test_exception_during_parsing_with_fallback(self):
        """Test that exceptions during parsing use fallback."""
        class BrokenMessage:
            @property
            def content(self):
                raise RuntimeError("Simulated error")
        
        messages = [BrokenMessage()]
        result = safe_parse_response(messages, "test_agent", fallback="Safe fallback")
        assert result == "Safe fallback"

