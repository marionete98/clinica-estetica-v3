# Agent Orchestrator - Escalation Interface Update

## Overview

The Agent Orchestrator has been updated to use the new structured interface for the Escalation Agent. This change improves clarity, maintainability, and provides better context for human agents.

**Date:** October 16, 2025  
**Component:** `services/agent_orchestrator.py`  
**Related Agent:** `agents/escalation.py`

## Changes Made

### 1. Contact Info Preparation

The orchestrator now prepares structured contact information before calling the escalation agent:

```python
# Prepare contact info for escalation
contact_info = {
    "phone": phone,
    "name": "Não informado",  # Would be extracted from context if available
    "email": "Não informado",
    "id": "N/A"
}
```

**Future Enhancement:** Extract name and email from conversation context when available.

### 2. Updated Method Call

The `prepare_escalation()` call now uses named parameters in a more logical order:

**Before:**
```python
response_data = await self.escalation.prepare_escalation(
    conversation_id=conversation_id,
    phone=phone,
    context=context_escalation,
    reason="loop_detected" if loop_detected else "user_request"
)
```

**After:**
```python
response_data = await self.escalation.prepare_escalation(
    reason="loop_detected" if loop_detected else "user_request",
    conversation_id=conversation_id,
    contact_info=contact_info,
    context=context_escalation
)
```

### 3. Response Handling

The orchestrator correctly extracts the patient message from the escalation response:

```python
if agent_name == "escalation":
    # Escalation agent returns "patient_message" instead of "response"
    response_text = response_data.get("patient_message", response_data.get("response", ""))
    should_escalate = response_data.get("should_pause_automation", True)
else:
    response_text = response_data.get("response", response_data.get("answer", ""))
    should_escalate = response_data.get("should_escalate", False)
```

## Benefits

### 1. Clearer Interface

The new interface makes it immediately clear what information is being passed:
- `reason`: Why escalation is happening
- `conversation_id`: Which conversation
- `contact_info`: Who is the patient (structured)
- `context`: Conversation history

### 2. Better Context for Human Agents

The structured `contact_info` provides human agents with:
- Phone number (always available from WhatsApp)
- Name (when collected by Intake Agent)
- Email (when provided by patient)
- Contact ID (for database lookups)

### 3. Extensibility

The structured format makes it easy to add more fields in the future:
```python
contact_info = {
    "phone": phone,
    "name": extracted_name,
    "email": extracted_email,
    "id": contact_id,
    "preferred_language": "pt-BR",  # Future addition
    "vip_status": False,  # Future addition
    "previous_escalations": 0  # Future addition
}
```

### 4. Priority Support

The interface now supports explicit priority levels:
- `"low"`: General inquiries, can wait
- `"medium"`: Standard escalations (default)
- `"high"`: Urgent issues, complaints, loops

## Context Extraction (Future Enhancement)

Currently, contact info uses placeholder values. Future enhancement will extract from context:

```python
def _extract_contact_info_from_context(
    phone: str,
    context: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Extract contact information from conversation context."""
    contact_info = {
        "phone": phone,
        "name": "Não informado",
        "email": "Não informado",
        "id": "N/A"
    }
    
    # Search context for name
    for msg in context:
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            # Look for "meu nome é [name]" pattern
            if "meu nome é" in content or "me chamo" in content:
                # Extract name (simplified)
                name = extract_name_from_message(content)
                if name:
                    contact_info["name"] = name
                    break
    
    # Search context for email
    for msg in context:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Look for email pattern
            email = extract_email_from_message(content)
            if email:
                contact_info["email"] = email
                break
    
    # Query database for contact ID
    try:
        contact = await get_contact_by_phone(phone)
        if contact:
            contact_info["id"] = contact.id
            contact_info["name"] = contact.name or contact_info["name"]
            contact_info["email"] = contact.email or contact_info["email"]
    except Exception as e:
        logger.warning(f"Could not fetch contact from database: {e}")
    
    return contact_info
```

## Testing

### Unit Tests

Test the orchestrator's escalation handling:

```python
@pytest.mark.asyncio
async def test_orchestrator_escalation_with_structured_contact():
    """Test orchestrator passes structured contact info to escalation."""
    orchestrator = AgentOrchestrator()
    
    # Mock escalation agent
    mock_escalation = AsyncMock()
    mock_escalation.prepare_escalation.return_value = {
        "patient_message": "Vou transferir você...",
        "summary": "Resumo completo",
        "should_pause_automation": True,
        "priority": "medium"
    }
    orchestrator.escalation = mock_escalation
    
    # Trigger escalation
    result = await orchestrator.orchestrate(
        conversation_id="test_123",
        phone="+5594991398585",
        message="Quero falar com alguém"
    )
    
    # Verify escalation was called with structured contact_info
    mock_escalation.prepare_escalation.assert_called_once()
    call_args = mock_escalation.prepare_escalation.call_args
    
    assert "contact_info" in call_args.kwargs
    assert call_args.kwargs["contact_info"]["phone"] == "+5594991398585"
    assert "reason" in call_args.kwargs
    assert call_args.kwargs["reason"] in ["loop_detected", "user_request"]
```

### Integration Tests

Test full escalation flow:

```python
@pytest.mark.asyncio
async def test_full_escalation_flow():
    """Test complete escalation flow with real agents."""
    orchestrator = get_orchestrator()
    
    # Simulate conversation leading to escalation
    messages = [
        "Olá",
        "João Silva",
        "Quanto custa laser?",
        "Quero falar com alguém"
    ]
    
    for message in messages:
        result = await orchestrator.orchestrate(
            conversation_id="test_escalation",
            phone="+5594991398585",
            message=message
        )
    
    # Last message should trigger escalation
    assert result["agent"] == "escalation"
    assert result["should_escalate"] is True
    assert "patient_message" in result or "response" in result
```

## Migration Notes

### For Developers

If you're working with the escalation agent directly:

1. **Update method calls** to use the new interface
2. **Prepare contact_info** as a dictionary before calling
3. **Extract patient_message** from response (not `response` key)
4. **Check should_pause_automation** flag (not `should_escalate`)

### For Operators

No changes to operation or monitoring:
- Escalations work the same way from user perspective
- Human agents receive better-formatted summaries
- Priority levels help with triaging

## References

- [Escalation Agent Documentation](AGENTS_GUIDE.md#5-escalation-agent)
- [AutoGen Migration Guide](AUTOGEN_MIGRATION_GUIDE.md)
- [Agent Orchestrator Source](../services/agent_orchestrator.py)
- [Escalation Agent Source](../agents/escalation.py)
