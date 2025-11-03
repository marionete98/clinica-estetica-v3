"""
Knowledge base and message template tools for AutoGen agents.
Provides functions for searching clinic information and retrieving message templates.
Requirements: 5.1, 5.2, 5.4
"""

import logging
from typing import List, Dict, Any, Optional

from models.repositories.knowledge_base import (
    get_message_template as repo_get_message_template,
    search_knowledge_base as repo_search_knowledge_base,
)

logger = logging.getLogger(__name__)


async def search_knowledge_base(
    query: str,
    top_k: int = 3,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search the clinic's knowledge base for relevant information.
    
    This function performs keyword-based search on the knowledge base,
    which contains information about treatments, procedures, policies,
    contraindications, and post-treatment care.
    
    Requirements: 5.1, 5.2, 5.4
    
    Args:
        query: Search query (will be split into keywords)
        top_k: Maximum number of results to return (default: 3)
        category: Optional category filter (e.g., 'treatments', 'policies')
        
    Returns:
        List of knowledge base entries, each containing:
        {
            "id": "uuid",
            "title": "Depilação a Laser - Informações Gerais",
            "content": "Detailed information about the treatment...",
            "category": "treatments",
            "keywords": ["laser", "depilação", "remoção de pelos"],
            "version": "1.0",
            "created_at": "2025-10-16T10:00:00Z",
            "updated_at": "2025-10-16T10:00:00Z"
        }
        
    Example:
        results = await search_knowledge_base("depilação laser preço")
        # Returns articles about laser hair removal and pricing
    """
    try:
        # Extract keywords from query
        # Simple approach: split by spaces and filter short words
        keywords = [
            word.lower().strip()
            for word in query.split()
            if len(word.strip()) >= 3
        ]
        
        if not keywords:
            logger.warning(f"No valid keywords extracted from query: {query}")
            return []
        
        logger.info(
            f"Searching knowledge base: query='{query}', "
            f"keywords={keywords}, category={category}, top_k={top_k}"
        )
        
        # Search knowledge base
        results = await repo_search_knowledge_base(
            keywords=keywords,
            category=category
        )
        
        # Convert to dictionaries and limit to top_k
        kb_entries = []
        for kb in results[:top_k]:
            entry = {
                "id": str(kb.id),
                "title": kb.title,
                "content": kb.content,
                "category": kb.category,
                "keywords": kb.keywords or [],
                "version": kb.version,
                "created_at": kb.created_at.isoformat() if kb.created_at else None,
                "updated_at": kb.updated_at.isoformat() if kb.updated_at else None
            }
            kb_entries.append(entry)
        
        logger.info(
            f"Found {len(kb_entries)} knowledge base entries for query: {query}"
        )
        
        return kb_entries
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise


async def get_message_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a predefined message template by name.
    
    Message templates are used for standardized communications such as:
    - Booking confirmations
    - Cancellation policies
    - Treatment rules and guidelines
    - Post-treatment care instructions
    
    Requirements: 5.2, 5.4
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Dictionary with template information or None if not found:
        {
            "id": "uuid",
            "name": "REGRAS_AGENDAMENTO_LASER",
            "content": "Template content with {variable} placeholders...",
            "variables": ["name", "date", "time"],
            "category": "policies",
            "active": true
        }
        
    Example:
        template = await get_message_template("REGRAS_AGENDAMENTO_LASER")
        # Returns the laser booking rules template
    """
    try:
        logger.info(f"Retrieving message template: {template_name}")
        
        # Retrieve template
        template = await repo_get_message_template(template_name)
        
        if template is None:
            logger.warning(f"Message template not found: {template_name}")
            return None
        
        # Convert to dictionary
        result = {
            "id": str(template.id),
            "name": template.name,
            "content": template.content,
            "variables": template.variables or [],
            "category": template.category,
            "active": template.active
        }
        
        logger.info(f"Retrieved message template: {template_name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving message template: {e}")
        raise


async def list_available_templates(category: Optional[str] = None) -> List[str]:
    """
    List available message template names.
    
    This is a helper function for agents to discover what templates are available.
    
    Args:
        category: Optional category filter
        
    Returns:
        List of template names
    """
    try:
        from config.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        
        query = supabase.table('message_templates').select('name').eq('active', True)
        
        if category:
            query = query.eq('category', category)
        
        response = query.execute()
        
        template_names = [row['name'] for row in response.data]
        
        logger.info(
            f"Listed {len(template_names)} message templates "
            f"(category={category})"
        )
        
        return template_names
        
    except Exception as e:
        logger.error(f"Error listing message templates: {e}")
        raise


async def format_template(
    template_name: str,
    variables: Dict[str, str]
) -> Optional[str]:
    """
    Retrieve and format a message template with provided variables.
    
    This is a convenience function that combines template retrieval
    and variable substitution.
    
    Args:
        template_name: Name of the template
        variables: Dictionary of variable name -> value mappings
        
    Returns:
        Formatted message string or None if template not found
        
    Example:
        message = await format_template(
            "CONFIRMACAO_AGENDAMENTO",
            {
                "name": "João Silva",
                "date": "17/10/2025",
                "time": "14:00",
                "procedure": "Botox"
            }
        )
    """
    try:
        template = await get_message_template(template_name)
        
        if template is None:
            return None
        
        content = template["content"]
        
        # Replace variables in template
        # Format: {variable_name}
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            content = content.replace(placeholder, str(var_value))
        
        logger.info(
            f"Formatted template {template_name} with variables: "
            f"{list(variables.keys())}"
        )
        
        return content
        
    except Exception as e:
        logger.error(f"Error formatting template: {e}")
        raise


# Tool metadata for AutoGen registration
KB_TOOLS = {
    "search_knowledge_base": {
        "function": search_knowledge_base,
        "description": (
            "Search the clinic's knowledge base for information about treatments, "
            "procedures, policies, contraindications, and post-treatment care. "
            "Use this when a patient asks questions about services, prices, or policies."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'depilação laser preço')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 3)",
                    "default": 3
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g., 'treatments', 'policies')"
                }
            },
            "required": ["query"]
        }
    },
    "get_message_template": {
        "function": get_message_template,
        "description": (
            "Retrieve a predefined message template for standardized communications. "
            "Use this for booking confirmations, policy explanations, and treatment guidelines."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Name of the template (e.g., 'REGRAS_AGENDAMENTO_LASER')"
                }
            },
            "required": ["template_name"]
        }
    },
    "format_template": {
        "function": format_template,
        "description": (
            "Retrieve and format a message template with provided variables. "
            "Use this to generate personalized messages from templates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Name of the template"
                },
                "variables": {
                    "type": "object",
                    "description": "Dictionary of variable name -> value mappings"
                }
            },
            "required": ["template_name", "variables"]
        }
    }
}
