"""
Testes para validar a migração para Semantic Kernel.
Verifica se todos os agentes podem ser importados e inicializados.
"""

import pytest
from unittest.mock import Mock, patch


def test_imports_semantic_kernel_components():
    """Valida que todos os componentes do Semantic Kernel podem ser importados."""
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    from semantic_kernel import Kernel
    from semantic_kernel.memory.null_memory import NullMemory
    from semantic_kernel.connectors.ai.google.google_ai import (
        GoogleAIChatCompletion,
        GoogleAIChatPromptExecutionSettings,
    )
    from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
        OpenAIChatCompletion,
    )
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIChatPromptExecutionSettings,
    )
    
    # Se chegou aqui, todos os imports funcionaram
    assert SKChatCompletionAdapter is not None
    assert Kernel is not None
    assert NullMemory is not None
    assert GoogleAIChatCompletion is not None
    assert GoogleAIChatPromptExecutionSettings is not None
    assert OpenAIChatCompletion is not None
    assert OpenAIChatPromptExecutionSettings is not None


def test_faq_agent_has_sk_create_method():
    """Valida que FAQAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.faq import FAQAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(FAQAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(FAQAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_supervisor_agent_has_sk_create_method():
    """Valida que SupervisorAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.supervisor import SupervisorAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(SupervisorAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(SupervisorAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_intake_agent_has_sk_create_method():
    """Valida que IntakeAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.intake import IntakeAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(IntakeAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(IntakeAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_scheduler_agent_has_sk_create_method():
    """Valida que SchedulerAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.scheduler import SchedulerAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(SchedulerAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(SchedulerAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_escalation_agent_has_sk_create_method():
    """Valida que EscalationAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.escalation import EscalationAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(EscalationAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(EscalationAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_followup_agent_has_sk_create_method():
    """Valida que FollowupAgent tem o método _create_model_client que retorna SKChatCompletionAdapter."""
    from agents.followup import FollowupAgent
    from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
    import inspect
    
    # Verifica que o método existe
    assert hasattr(FollowupAgent, '_create_model_client')
    
    # Verifica a assinatura do método
    sig = inspect.signature(FollowupAgent._create_model_client)
    assert sig.return_annotation.__name__ == 'SKChatCompletionAdapter'


def test_no_legacy_openai_client_imports_in_agents():
    """Valida que nenhum agente importa OpenAIChatCompletionClient (legacy)."""
    import os
    import re
    
    agents_dir = "agents"
    legacy_import_pattern = re.compile(r'from\s+autogen_ext\.models\.openai\s+import\s+OpenAIChatCompletionClient')
    
    for filename in os.listdir(agents_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(agents_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                assert not legacy_import_pattern.search(content), \
                    f"Encontrado import legacy em {filename}: OpenAIChatCompletionClient"


def test_all_agents_import_sk_adapter():
    """Valida que todos os agentes importam SKChatCompletionAdapter."""
    import os
    import re
    
    agents_dir = "agents"
    sk_import_pattern = re.compile(r'from\s+autogen_ext\.models\.semantic_kernel\s+import\s+SKChatCompletionAdapter')
    
    agent_files = ['faq.py', 'supervisor.py', 'intake.py', 'scheduler.py', 'escalation.py', 'followup.py']
    
    for filename in agent_files:
        filepath = os.path.join(agents_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert sk_import_pattern.search(content), \
                f"SKChatCompletionAdapter não encontrado em {filename}"
