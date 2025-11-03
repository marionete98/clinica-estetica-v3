# AutoGen Code Review - Detailed Findings & Recommendations

## Part 1: Critical Issues Requiring Immediate Action

### Issue 1.1: AutoGen Version and Packages Verification (RESOLVED/OK)

**Location:** `requirements.txt:21`

**Current State:**
```txt
pyautogen==0.7.5
```

**Facts:**
- `pyautogen` on PyPI is a proxy package for the latest `autogen-agentchat` releases.
- The code imports `autogen_agentchat`, `autogen_core`, and `autogen_ext`, which are the correct modules for AgentChat 0.7.x.
- Official docs recommend installing `autogen-agentchat` and `autogen-ext[openai]` directly.

**Evidence:**
- Docs: https://microsoft.github.io/autogen/stable/
- PyPI (pyautogen): https://pypi.org/project/pyautogen/
- PyPI (autogen-agentchat): https://pypi.org/project/autogen-agentchat/

```python
# agents/supervisor.py (imports in this codebase)
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken
```

**Resolution:**
- No change required. Optionally replace the proxy with explicit dependencies for clarity:
  - `autogen-agentchat==0.7.5`
  - `autogen-ext[openai]`
  - (`autogen-core` is a transitive dependency)

**Verification:**
```bash
python - <<'PY'
import importlib
for m in [
    'autogen_agentchat.agents',
    'autogen_agentchat.messages',
    'autogen_ext.models.openai',
    'autogen_core']:
    importlib.import_module(m)
print('AutoGen imports OK')
PY
```

---

### Issue 1.2: Syntax Error in Agent Orchestrator (CRITICAL)

**Location:** `services/agent_orchestrator.py:136-195`

**Problem:**
Indentation error in `_load_context_from_redis` method - code is indented inside try block instead of being at method level.

**Current (WRONG):**
```python
async def _load_context_from_redis(self, conversation_id: str, max_messages: int = 8):
    try:
        context_key = f"conv:{conversation_id}"
        
        # Line 136 - WRONG INDENTATION
                messages = await self.redis_client.get_context(...)  # Extra indent!
                
                if messages:
                    logger.info(...)
                else:
                    logger.info(...)
        
        return messages or []
    
    except Exception as e:
        logger.warning(...)
        return []

# Line 160 - WRONG: This method is indented inside the try block!
async def _update_context_in_redis(self, ...):
    ...
```

**Correct:**
```python
async def _load_context_from_redis(self, conversation_id: str, max_messages: int = 8):
    try:
        context_key = f"conv:{conversation_id}"
        messages = await self.redis_client.get_context(
            conversation_id,
            max_messages=max_messages
        )
        
        if messages:
            logger.info(f"Loaded {len(messages)} messages...")
        else:
            logger.info(f"No context found...")
        
        return messages or []
        
    except Exception as e:
        logger.warning(f"Failed to load context: {e}")
        return []

async def _update_context_in_redis(self, conversation_id: str, ...):
    """Update conversation context in Redis."""
    try:
        await self.redis_client.append_message(...)
        await self.redis_client.append_message(...)
        logger.info(f"Updated context in Redis...")
    except Exception as e:
        logger.error(f"Failed to update context: {e}", exc_info=True)
```

**Impact:** File will not import; Python syntax error

---

### Issue 1.3: Fragile Response Parsing Pattern (HIGH)

**Location:** Multiple files
- `agents/supervisor.py:257-260`
- `agents/faq.py:426-431`
- `agents/scheduler.py:269-274`
- `agents/escalation.py:350-354`

**Problem:**
Response parsing uses hasattr checks without type validation or error handling.

**Current (FRAGILE):**
```python
def _parse_response(self, response) -> str:
    if hasattr(response, 'chat_message'):
        return response.chat_message.content
    elif hasattr(response, 'content'):
        return response.content
    else:
        return str(response)
```

**Issues:**
1. No type checking - could match unintended objects
2. No null checks - `response.chat_message` could be None
3. No error handling - AttributeError not caught
4. No logging - can't debug unexpected response types
5. Falls back to str() which may produce garbage

**Recommended Solution:**
```python
from typing import Union
from autogen_agentchat.agents import Response

def _parse_response(self, response: Union[Response, str]) -> str:
    """
    Parse AutoGen 0.4 Response object to extract text.
    
    Args:
        response: Response object from agent.on_messages()
        
    Returns:
        Response text as string
        
    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        # Handle string responses directly
        if isinstance(response, str):
            return response
        
        # Handle Response objects from AutoGen 0.4
        if hasattr(response, 'chat_message'):
            if response.chat_message is None:
                logger.warning("Response.chat_message is None")
                return ""
            if hasattr(response.chat_message, 'content'):
                content = response.chat_message.content
                if isinstance(content, str):
                    return content
                logger.warning(f"Unexpected content type: {type(content)}")
                return str(content)
        
        # Fallback for other response types
        if hasattr(response, 'content'):
            return str(response.content)
        
        # Last resort
        logger.warning(f"Unknown response type: {type(response)}, converting to string")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error parsing response: {e}", exc_info=True)
        raise ValueError(f"Failed to parse response: {e}")
```

---

## Part 2: High Priority Issues

### Issue 2.1: Missing Resource Cleanup in Error Paths

**Location:** All agent methods that use `CancellationToken`

**Problem:**
CancellationToken and model client resources not cleaned up on exceptions.

**Example (agents/faq.py:467-550):**
```python
async def answer_question(self, question: str, ...):
    try:
        # ... setup code ...
        cancellation_token = CancellationToken()
        text_message = TextMessage(content=prompt, source="user")
        response = await self.agent.on_messages([text_message], cancellation_token)
        # ... processing ...
    except Exception as e:
        logger.error(f"Error: {e}")
        # MISSING: Resource cleanup!
        raise
```

**Recommended Fix:**
```python
async def answer_question(self, question: str, ...):
    cancellation_token = CancellationToken()
    try:
        text_message = TextMessage(content=prompt, source="user")
        response = await self.agent.on_messages([text_message], cancellation_token)
        # ... processing ...
        return result
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise
    finally:
        # Ensure cancellation token is cancelled
        try:
            await cancellation_token.cancel()
        except Exception as e:
            logger.warning(f"Error cancelling token: {e}")
```

---

### Issue 2.2: Incomplete Tool Definitions

**Location:** `tools/kb_tools_cached.py:13-66`

**Problem:**
Tools lack proper type hints and docstrings for AutoGen 0.4 schema generation.

**Current:**
```python
async def search_knowledge_base(
    query: str,
    top_k: int = 3,
    category: Optional[str] = None
) -> tuple[List[Dict[str, Any]], List[str]]:
    """Search knowledge base using Redis cache."""
```

**Issues:**
1. Return type is tuple - AutoGen expects single return value
2. Missing detailed docstring for schema generation
3. No parameter descriptions
4. No error documentation

**Recommended:**
```python
async def search_knowledge_base(
    query: str,
    top_k: int = 3,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search the knowledge base for relevant information.
    
    This tool searches the Redis-cached knowledge base using keyword matching
    and returns the most relevant results ranked by relevance score.
    
    Args:
        query: The search query (e.g., "depilação laser preço")
        top_k: Maximum number of results to return (default: 3, max: 10)
        category: Optional category filter (e.g., "Tratamentos", "policy")
    
    Returns:
        Dictionary with:
        - results: List of matching KB entries with relevance scores
        - sources: List of source titles
        - count: Number of results found
        - query: Original query
    
    Raises:
        ValueError: If query is empty or invalid
        ConnectionError: If Redis connection fails
    
    Examples:
        >>> result = await search_knowledge_base("laser hair removal")
        >>> print(result['count'])  # Number of results
        >>> for entry in result['results']:
        ...     print(entry['title'], entry['relevance_score'])
    """
    try:
        logger.info(f"Searching KB: query='{query}', category={category}")
        
        # ... implementation ...
        
        return {
            "results": results,
            "sources": sources,
            "count": len(results),
            "query": query,
            "category": category
        }
    except Exception as e:
        logger.error(f"KB search error: {e}")
        raise
```

---

## Part 3: Medium Priority Issues

### Issue 3.1: Missing Type Hints

**Locations:**
- `agents/faq.py:416` - `_parse_response` missing return type
- `agents/scheduler.py:259` - `_parse_response` missing return type
- `agents/escalation.py:149` - `_create_model_client` missing return type

**Recommendation:** Add complete type hints to all methods

### Issue 3.2: Incomplete Followup Agent

**Location:** `agents/followup.py`

**Status:** Only docstring visible, implementation not shown in review

**Action:** Verify implementation is complete and follows AutoGen 0.7.x patterns


