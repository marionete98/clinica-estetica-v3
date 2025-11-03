"""
Tests for input validation models.

This module tests the Pydantic validation models in models/validation.py,
ensuring robust input validation for webhook payloads and contact information.

Test Coverage:
- Phone number validation (Brazilian format)
- Phone number normalization to E.164
- Message sanitization (control characters)
- Conversation ID validation
- Sender validation
- Email validation
- Edge cases (None, empty, very long inputs)

Requirements: Phase 1, Task 1.4
"""

import pytest
from pydantic import ValidationError
from models.validation import ChatwootMessageInput, ContactInput


class TestChatwootMessageInputPhoneValidation:
    """Tests for phone number validation in ChatwootMessageInput."""
    
    def test_valid_phone_e164_format(self):
        """Test valid phone in E.164 format (+5511999999999)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.phone == "+5511999999999"
    
    def test_valid_phone_with_formatting(self):
        """Test valid phone with formatting (11) 99999-9999."""
        data = {
            "conversation_id": "12345",
            "phone": "(11) 99999-9999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.phone == "+5511999999999"
    
    def test_valid_phone_without_country_code(self):
        """Test valid phone without country code (11999999999)."""
        data = {
            "conversation_id": "12345",
            "phone": "11999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.phone == "+5511999999999"
    
    def test_valid_phone_with_spaces(self):
        """Test valid phone with spaces (+55 11 99999-9999)."""
        data = {
            "conversation_id": "12345",
            "phone": "+55 11 99999-9999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.phone == "+5511999999999"
    
    def test_valid_phone_different_ddd(self):
        """Test valid phone with different DDD (area code)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5521987654321",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.phone == "+5521987654321"
    
    def test_invalid_phone_too_short(self):
        """Test invalid phone (too short)."""
        data = {
            "conversation_id": "12345",
            "phone": "123456",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("phone" in str(e) for e in errors)
    
    def test_invalid_phone_letters(self):
        """Test invalid phone (contains letters)."""
        data = {
            "conversation_id": "12345",
            "phone": "11abc999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("phone" in str(e) for e in errors)
    
    def test_invalid_phone_wrong_country_code(self):
        """Test invalid phone (wrong country code)."""
        data = {
            "conversation_id": "12345",
            "phone": "+1234567890",  # US number
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)

        errors = exc_info.value.errors()
        assert any("phone" in str(e) for e in errors)
    
    def test_invalid_phone_empty(self):
        """Test invalid phone (empty string)."""
        data = {
            "conversation_id": "12345",
            "phone": "",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("phone" in str(e) for e in errors)
    
    def test_invalid_phone_whitespace_only(self):
        """Test invalid phone (whitespace only)."""
        data = {
            "conversation_id": "12345",
            "phone": "   ",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("phone" in str(e) for e in errors)


class TestChatwootMessageInputMessageSanitization:
    """Tests for message sanitization in ChatwootMessageInput."""
    
    def test_valid_message_simple(self):
        """Test valid simple message."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Olá, gostaria de agendar",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "Olá, gostaria de agendar"
    
    def test_message_with_newlines(self):
        """Test message with newlines (should be preserved)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Linha 1\nLinha 2\nLinha 3",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "Linha 1\nLinha 2\nLinha 3"
    
    def test_message_with_tabs(self):
        """Test message with tabs (should be preserved)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Item 1\tItem 2\tItem 3",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "Item 1\tItem 2\tItem 3"
    
    def test_message_removes_control_characters(self):
        """Test that control characters are removed."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello\x00World\x01Test\x1F",  # Contains null, SOH, US
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "HelloWorldTest"
        assert "\x00" not in result.message
        assert "\x01" not in result.message
        assert "\x1F" not in result.message
    
    def test_message_removes_extended_control_chars(self):
        """Test that extended control characters (0x7F-0x9F) are removed."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Test\x7FMessage\x80Here\x9F",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "TestMessageHere"
    
    def test_message_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "   Hello World   ",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "Hello World"
    
    def test_message_unicode_preserved(self):
        """Test that Unicode characters are preserved."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Olá! 你好 🎉 Здравствуйте",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.message == "Olá! 你好 🎉 Здравствуйте"
    
    def test_message_too_long(self):
        """Test message exceeding max length (4000 chars)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "A" * 4001,
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("message" in str(e) for e in errors)
    
    def test_message_empty(self):
        """Test empty message."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("message" in str(e) for e in errors)
    
    def test_message_only_control_chars(self):
        """Test message with only control characters."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "\x00\x01\x02\x03",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)
        
        errors = exc_info.value.errors()
        assert any("message" in str(e) for e in errors)
        assert any("empty" in str(e).lower() for e in errors)


class TestChatwootMessageInputConversationID:
    """Tests for conversation ID validation."""
    
    def test_valid_conversation_id_numeric(self):
        """Test valid numeric conversation ID."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.conversation_id == "12345"
    
    def test_valid_conversation_id_alphanumeric(self):
        """Test valid alphanumeric conversation ID."""
        data = {
            "conversation_id": "conv-abc123-xyz",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.conversation_id == "conv-abc123-xyz"
    
    def test_valid_conversation_id_with_underscore(self):
        """Test valid conversation ID with underscores."""
        data = {
            "conversation_id": "conv_123_abc",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.conversation_id == "conv_123_abc"
    
    def test_conversation_id_strips_whitespace(self):
        """Test that conversation ID strips whitespace."""
        data = {
            "conversation_id": "  12345  ",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.conversation_id == "12345"
    
    def test_invalid_conversation_id_empty(self):
        """Test invalid empty conversation ID."""
        data = {
            "conversation_id": "",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)
    
    def test_invalid_conversation_id_whitespace_only(self):
        """Test invalid conversation ID (whitespace only)."""
        data = {
            "conversation_id": "   ",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)
    
    def test_invalid_conversation_id_special_chars(self):
        """Test invalid conversation ID with special characters."""
        data = {
            "conversation_id": "conv@123#abc",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)
    
    def test_invalid_conversation_id_too_long(self):
        """Test invalid conversation ID (too long)."""
        data = {
            "conversation_id": "a" * 51,
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)


class TestChatwootMessageInputSenderValidation:
    """Tests for sender validation."""

    def test_valid_sender_minimal(self):
        """Test valid sender with minimal fields."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.sender == {"id": 1}

    def test_valid_sender_full(self):
        """Test valid sender with all fields."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {
                "id": 1,
                "name": "João Silva",
                "email": "joao@example.com",
                "phone": "+5511999999999"
            }
        }
        result = ChatwootMessageInput(**data)
        assert result.sender["id"] == 1
        assert result.sender["name"] == "João Silva"

    def test_invalid_sender_empty_dict(self):
        """Test invalid sender (empty dictionary)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)

        errors = exc_info.value.errors()
        assert any("sender" in str(e) for e in errors)

    def test_invalid_sender_missing_id(self):
        """Test invalid sender (missing id field)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"name": "João"}
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatwootMessageInput(**data)

        errors = exc_info.value.errors()
        assert any("sender" in str(e) for e in errors)


class TestChatwootMessageInputTimestamp:
    """Tests for timestamp validation."""

    def test_valid_timestamp(self):
        """Test valid timestamp."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert result.timestamp == 1697500000

    def test_invalid_timestamp_zero(self):
        """Test invalid timestamp (zero)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 0,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)

    def test_invalid_timestamp_negative(self):
        """Test invalid timestamp (negative)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": -1,
            "sender": {"id": 1}
        }
        with pytest.raises(ValidationError):
            ChatwootMessageInput(**data)


class TestContactInputValidation:
    """Tests for ContactInput validation model."""

    def test_valid_contact_full(self):
        """Test valid contact with all fields."""
        data = {
            "phone": "+5511999999999",
            "name": "Maria Silva",
            "email": "maria@example.com",
            "consent": True
        }
        result = ContactInput(**data)
        assert result.phone == "+5511999999999"
        assert result.name == "Maria Silva"
        assert result.email == "maria@example.com"
        assert result.consent is True

    def test_valid_contact_minimal(self):
        """Test valid contact with minimal fields."""
        data = {
            "phone": "+5511999999999"
        }
        result = ContactInput(**data)
        assert result.phone == "+5511999999999"
        assert result.name is None
        assert result.email is None
        assert result.consent is False

    def test_valid_contact_phone_normalization(self):
        """Test phone normalization in ContactInput."""
        data = {
            "phone": "(11) 99999-9999"
        }
        result = ContactInput(**data)
        assert result.phone == "+5511999999999"

    def test_valid_email(self):
        """Test valid email validation."""
        data = {
            "phone": "+5511999999999",
            "email": "test@example.com"
        }
        result = ContactInput(**data)
        assert result.email == "test@example.com"

    def test_invalid_email(self):
        """Test invalid email."""
        data = {
            "phone": "+5511999999999",
            "email": "not-an-email"
        }
        with pytest.raises(ValidationError) as exc_info:
            ContactInput(**data)

        errors = exc_info.value.errors()
        assert any("email" in str(e) for e in errors)

    def test_name_sanitization(self):
        """Test name sanitization (removes control chars)."""
        data = {
            "phone": "+5511999999999",
            "name": "João\x00Silva\x01"
        }
        result = ContactInput(**data)
        assert result.name == "JoãoSilva"
        assert "\x00" not in result.name

    def test_name_empty_after_sanitization(self):
        """Test name becomes None if empty after sanitization."""
        data = {
            "phone": "+5511999999999",
            "name": "\x00\x01\x02"
        }
        result = ContactInput(**data)
        assert result.name is None

    def test_invalid_phone_in_contact(self):
        """Test invalid phone in ContactInput."""
        data = {
            "phone": "invalid"
        }
        with pytest.raises(ValidationError):
            ContactInput(**data)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_message_exactly_4000_chars(self):
        """Test message with exactly 4000 characters (max length)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "A" * 4000,
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert len(result.message) == 4000

    def test_conversation_id_exactly_50_chars(self):
        """Test conversation ID with exactly 50 characters (max length)."""
        data = {
            "conversation_id": "a" * 50,
            "phone": "+5511999999999",
            "message": "Hello",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert len(result.conversation_id) == 50

    def test_phone_various_brazilian_formats(self):
        """Test various valid Brazilian phone formats."""
        formats = [
            "+5511999999999",
            "5511999999999",
            "11999999999",
            "(11) 99999-9999",
            "+55 11 99999-9999",
            "11 99999-9999",
            "+55 (11) 99999-9999"
        ]

        for phone_format in formats:
            data = {
                "conversation_id": "12345",
                "phone": phone_format,
                "message": "Hello",
                "timestamp": 1697500000,
                "sender": {"id": 1}
            }
            result = ChatwootMessageInput(**data)
            assert result.phone == "+5511999999999", f"Failed for format: {phone_format}"

    def test_message_with_mixed_content(self):
        """Test message with mixed content (text, emojis, newlines)."""
        data = {
            "conversation_id": "12345",
            "phone": "+5511999999999",
            "message": "Olá! 😊\n\nGostaria de:\n1. Agendar consulta\n2. Ver preços\n\nObrigado! 🙏",
            "timestamp": 1697500000,
            "sender": {"id": 1}
        }
        result = ChatwootMessageInput(**data)
        assert "😊" in result.message
        assert "🙏" in result.message
        assert "\n" in result.message

    def test_all_fields_valid(self):
        """Test complete valid payload with all fields."""
        data = {
            "conversation_id": "conv-12345-abc",
            "phone": "+5521987654321",
            "message": "Olá, gostaria de agendar uma consulta para próxima semana.",
            "timestamp": 1697500000,
            "sender": {
                "id": 123,
                "name": "João Silva",
                "email": "joao@example.com",
                "phone": "+5521987654321"
            }
        }
        result = ChatwootMessageInput(**data)
        assert result.conversation_id == "conv-12345-abc"
        assert result.phone == "+5521987654321"
        assert "agendar" in result.message
        assert result.timestamp == 1697500000
        assert result.sender["id"] == 123

