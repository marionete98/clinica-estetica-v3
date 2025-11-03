"""
Testes estáticos para validar qualidade do prompt otimizado do INTAKE Agent.
Testa melhorias implementadas pelo Agent Lightning sem dependências externas.
"""

import pytest


# Import apenas o prompt, sem dependências
def get_intake_prompt():
    """Lê o prompt direto do arquivo para evitar dependências."""
    import re
    with open("agents/intake.py", "r", encoding="utf-8") as f:
        content = f.read()
        # Extrai o INTAKE_SYSTEM_PROMPT
        match = re.search(r'INTAKE_SYSTEM_PROMPT = """(.+?)"""', content, re.DOTALL)
        if match:
            return match.group(1)
    return ""


class TestIntakePromptQuality:
    """Testes de qualidade do prompt otimizado."""

    @pytest.fixture
    def prompt(self):
        """Carrega o prompt."""
        return get_intake_prompt()

    def test_prompt_exists(self, prompt):
        """Verifica que o prompt foi carregado."""
        assert prompt, "Prompt deve existir"
        assert len(prompt) > 500, "Prompt deve ter conteúdo substancial"

    def test_has_lgpd_compliance_instructions(self, prompt):
        """
        Verifica instruções de conformidade LGPD.
        Melhoria: Prompt otimizado adiciona consentimento explícito.
        """
        prompt_lower = prompt.lower()

        assert "consentimento" in prompt_lower or "consent" in prompt_lower, \
            "Deve mencionar consentimento"

        assert "explique por que" in prompt_lower or "sempre explique" in prompt_lower, \
            "Deve instruir a explicar por que dados são necessários"

        assert "peça consentimento" in prompt_lower or "pedir consentimento" in prompt_lower, \
            "Deve instruir a pedir consentimento antes de salvar"

    def test_has_proactive_behavior_instructions(self, prompt):
        """
        Verifica instruções de comportamento proativo.
        Melhoria: Prompt otimizado enfatiza proatividade.
        """
        prompt_lower = prompt.lower()

        assert "proativ" in prompt_lower, \
            "Deve mencionar comportamento proativo"

        assert ("ofereça" in prompt_lower or "sugira" in prompt_lower), \
            "Deve instruir a oferecer/sugerir próximos passos"

        proactive_examples = [
            "posso verificar horários",
            "deseja que eu agende",
            "posso te encaminhar",
        ]
        has_example = any(ex in prompt_lower for ex in proactive_examples)
        assert has_example, \
            "Deve ter exemplos de ofertas proativas"

    def test_has_detailed_conversation_flow(self, prompt):
        """
        Verifica fluxo de conversa detalhado.
        Melhoria: Prompt otimizado tem 7 passos ao invés de 5.
        """
        # Conta passos numerados
        import re
        steps = re.findall(r'\n\d+\)', prompt)

        assert len(steps) >= 7, \
            f"Deve ter pelo menos 7 passos detalhados (encontrado: {len(steps)})"

    def test_has_concrete_examples(self, prompt):
        """
        Verifica presença de exemplos concretos.
        Melhoria: Prompt otimizado inclui exemplos de saudação.
        """
        assert "Ex.:" in prompt or "exemplo" in prompt.lower() or "Ex:" in prompt, \
            "Deve incluir exemplos concretos"

        prompt_lower = prompt.lower()

        # Verifica exemplo de saudação
        greeting_indicators = [
            "olá! aqui é",
            "como posso te ajudar",
            "seja bem-vind",
        ]
        has_greeting = any(ind in prompt_lower for ind in greeting_indicators)
        assert has_greeting, \
            "Deve incluir exemplo de saudação"

    def test_has_short_scannable_messages_instruction(self, prompt):
        """
        Verifica instrução para mensagens curtas e escaneáveis.
        Melhoria: Prompt otimizado enfatiza mensagens facilmente escaneáveis.
        """
        prompt_lower = prompt.lower()

        scannable_keywords = [
            "parágrafos curtos",
            "mensagens facilmente escaneáveis",
            "frases curtas",
        ]

        assert any(kw in prompt_lower for kw in scannable_keywords), \
            "Deve instruir sobre mensagens curtas/escaneáveis"

    def test_forbids_sensitive_data_collection(self, prompt):
        """
        Verifica instrução para não coletar dados sensíveis.
        Melhoria: Prompt otimizado proíbe CPF, dados de saúde sem necessidade.
        """
        prompt_lower = prompt.lower()

        assert "não solicite dados sensíveis" in prompt_lower or \
               "não solicitar dados sensíveis" in prompt_lower, \
            "Deve proibir coleta de dados sensíveis"

        # Verifica menção específica de dados sensíveis
        sensitive_data_mentions = ["cpf", "saúde", "documentos"]
        has_mention = any(data in prompt_lower for data in sensitive_data_mentions)
        assert has_mention, \
            "Deve mencionar especificamente quais dados sensíveis evitar"

    def test_has_completion_marker_instruction(self, prompt):
        """
        Verifica instrução clara sobre INTAKE_COMPLETE.
        Melhoria: Prompt otimizado enfatiza string exata de completion.
        """
        assert "INTAKE_COMPLETE" in prompt, \
            "Deve mencionar o marker de completion"

        prompt_lower = prompt.lower()

        completion_instructions = [
            "retorne exatamente",
            "deve ser a string",
            "última saída",
        ]
        has_instruction = any(inst in prompt_lower for inst in completion_instructions)
        assert has_instruction, \
            "Deve ter instrução clara sobre quando retornar INTAKE_COMPLETE"

    def test_has_identity_confirmation_instruction(self, prompt):
        """
        Verifica instrução para confirmar identidade em cadastros duplicados.
        Melhoria: Prompt otimizado adiciona verificação de identidade.
        """
        prompt_lower = prompt.lower()

        identity_keywords = [
            "confirme o nome",
            "é você",
            "confirmação de identidade" "múltiplos cadastros",
        ]

        has_identity_check = any(kw in prompt_lower for kw in identity_keywords)
        assert has_identity_check, \
            "Deve instruir a confirmar identidade quando necessário"

    def test_has_tool_feedback_instruction(self, prompt):
        """
        Verifica instrução para feedback após chamadas de ferramentas.
        Melhoria: Prompt otimizado exige resposta natural após ferramentas.
        """
        prompt_lower = prompt.lower()

        feedback_keywords = [
            "após cada chamada de ferramenta",
            "retorne uma mensagem natural",
            "explique o resultado",
        ]

        has_feedback_instruction = any(kw in prompt_lower for kw in feedback_keywords)
        assert has_feedback_instruction, \
            "Deve instruir a dar feedback após cada ferramenta"

    def test_has_alternatives_for_reluctant_patients(self, prompt):
        """
        Verifica instrução para lidar com pacientes relutantes.
        Melhoria: Prompt otimizado oferece alternativas quando paciente não quer fornecer dados.
        """
        prompt_lower = prompt.lower()

        assert "não quiser fornecer" in prompt_lower or "não quer fornecer" in prompt_lower, \
            "Deve abordar cenário de paciente relutante"

        assert "ofereça alternativas" in prompt_lower or "continue a conversa" in prompt_lower, \
            "Deve instruir a oferecer alternativas"

        assert "sem pressionar" in prompt_lower, \
            "Deve instruir a não pressionar o paciente"

    def test_has_improved_tone_instructions(self, prompt):
        """
        Verifica instruções de tom melhoradas.
        Melhoria: Prompt otimizado tem linguagem mais profissional e detalhada.
        """
        prompt_lower = prompt.lower()

        # Verifica menção de linguagem profissional
        assert "profissional" in prompt_lower, \
            "Deve mencionar tom profissional"

        # Verifica instruções sobre emojis
        assert "emojis" in prompt_lower, \
            "Deve ter orientação sobre uso de emojis"

        # Verifica que orienta moderação
        moderation_keywords = ["moderação", "leves", "sem exagero"]
        has_moderation = any(kw in prompt_lower for kw in moderation_keywords)
        assert has_moderation, \
            "Deve orientar uso moderado de emojis"

    def test_has_expected_responses_section(self, prompt):
        """
        Verifica presença da seção 'Respostas esperadas'.
        Melhoria: Prompt otimizado adiciona seção explícita sobre output esperado.
        """
        assert "Respostas esperadas" in prompt or "respostas esperadas" in prompt.lower(), \
            "Deve ter seção de respostas esperadas"


class TestPromptComparison:
    """Testes comparativos para verificar melhorias sobre baseline."""

    @pytest.fixture
    def prompt(self):
        """Carrega o prompt atual."""
        return get_intake_prompt()

    def test_prompt_is_longer_than_baseline(self, prompt):
        """
        Verifica que prompt otimizado é mais detalhado que baseline.
        Baseline tinha ~600 caracteres, otimizado tem ~3000+.
        """
        assert len(prompt) > 2000, \
            f"Prompt otimizado deve ter mais de 2000 caracteres (atual: {len(prompt)})"

    def test_has_more_structure_than_baseline(self, prompt):
        """
        Verifica que prompt tem mais seções estruturadas.
        """
        sections = [
            "Linguagem & Tom",
            "Missão",
            "Ferramentas",
            "Fluxo de Conversa",
            "Boas Práticas",
            "Respostas esperadas",
        ]

        missing_sections = [s for s in sections if s not in prompt]

        assert not missing_sections, \
            f"Prompt deve ter todas as seções esperadas. Faltando: {missing_sections}"

    def test_comment_indicates_optimization(self, prompt):
        """
        Verifica que comentário indica que foi otimizado.
        """
        # Lê o arquivo completo para pegar o comentário
        with open("agents/intake.py", "r", encoding="utf-8") as f:
            content = f.read()

        assert "optimized" in content.lower() or "agent lightning" in content.lower(), \
            "Comentário deve indicar otimização com Agent Lightning"


class TestPromptMetrics:
    """Métricas quantitativas do prompt."""

    @pytest.fixture
    def prompt(self):
        """Carrega o prompt."""
        return get_intake_prompt()

    def test_character_count(self, prompt):
        """Verifica tamanho mínimo do prompt."""
        char_count = len(prompt)
        assert char_count >= 2500, \
            f"Prompt otimizado deve ter pelo menos 2500 caracteres (atual: {char_count})"

    def test_word_count(self, prompt):
        """Verifica contagem de palavras."""
        word_count = len(prompt.split())
        assert word_count >= 400, \
            f"Prompt otimizado deve ter pelo menos 400 palavras (atual: {word_count})"

    def test_line_count(self, prompt):
        """Verifica número de linhas."""
        line_count = len(prompt.split('\n'))
        assert line_count >= 40, \
            f"Prompt otimizado deve ter pelo menos 40 linhas (atual: {line_count})"

    def test_bullet_points_count(self, prompt):
        """Verifica uso de bullet points para clareza."""
        bullet_count = prompt.count('\n-')
        assert bullet_count >= 15, \
            f"Prompt deve usar bullet points para clareza (encontrado: {bullet_count})"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
