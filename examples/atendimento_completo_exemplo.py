"""
Exemplo Completo de Atendimento - Clínica Luana Multi-Agent System

Este exemplo demonstra um fluxo completo de atendimento via WhatsApp,
mostrando como o sistema processa mensagens, usa cache Redis, e coordena
múltiplos agentes.

Fluxo:
1. Paciente envia mensagem via WhatsApp
2. Chatwoot recebe e envia webhook
3. Sistema classifica intenção (Supervisor)
4. Agente apropriado processa (FAQ, Scheduler, etc.)
5. Cache Redis otimiza respostas repetidas
6. Resposta enviada via Chatwoot/WhatsApp
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

# Simulação dos componentes do sistema
class SimulatedSystem:
    """Simula o sistema completo para demonstração."""
    
    def __init__(self):
        self.conversation_history = []
        self.redis_cache = {}  # Simula Redis
        self.contact_info = None
        
    def log(self, step: str, message: str, details: Dict = None):
        """Log formatado para visualização."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {step}")
        print(f"  {message}")
        if details:
            for key, value in details.items():
                print(f"  • {key}: {value}")


async def exemplo_atendimento_completo():
    """
    Exemplo de atendimento completo com múltiplas interações.
    """
    
    system = SimulatedSystem()
    
    print("=" * 80)
    print("EXEMPLO DE ATENDIMENTO COMPLETO - CLÍNICA LUANA")
    print("=" * 80)
    print("\nPaciente: Maria Silva")
    print("Canal: WhatsApp via Chatwoot")
    print("Horário: 14:30")
    print("=" * 80)
    
    # ========================================================================
    # INTERAÇÃO 1: Pergunta sobre preço (FAQ)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("INTERAÇÃO 1: Pergunta sobre Preço")
    print("=" * 80)
    
    system.log(
        "📱 MENSAGEM RECEBIDA",
        "Paciente envia mensagem via WhatsApp",
        {
            "De": "Maria Silva (+55 11 98765-4321)",
            "Mensagem": "Oi! Quanto custa a depilação a laser?",
            "Timestamp": "14:30:15"
        }
    )
    
    system.log(
        "🔔 WEBHOOK CHATWOOT",
        "Chatwoot envia webhook para o sistema",
        {
            "Endpoint": "POST /webhooks/chatwoot",
            "conversation_id": "12345",
            "sender_id": "67890",
            "content": "Oi! Quanto custa a depilação a laser?"
        }
    )
    
    system.log(
        "🔍 REDIS - CONTEXTO",
        "Sistema busca histórico de conversação no Redis",
        {
            "Key": "conv:12345",
            "Resultado": "Nenhum histórico encontrado (primeira mensagem)",
            "TTL": "24 horas"
        }
    )
    
    system.log(
        "🤖 SUPERVISOR AGENT",
        "Classifica intenção da mensagem",
        {
            "Entrada": "Oi! Quanto custa a depilação a laser?",
            "Análise": "Pergunta sobre preço de tratamento",
            "Intenção": "FAQ",
            "Confiança": "95%",
            "Agente Selecionado": "FAQ Agent"
        }
    )
    
    system.log(
        "💾 REDIS - FAQ CACHE",
        "FAQ Agent verifica cache antes de chamar LLM",
        {
            "Pergunta": "Oi! Quanto custa a depilação a laser?",
            "Normalizada": "preço depilação laser",
            "Cache Key": "faq_cache:a1b2c3d4e5f6...",
            "Resultado": "MISS (primeira vez)",
            "Hit Rate": "0%"
        }
    )
    
    system.log(
        "🔎 KNOWLEDGE BASE",
        "Busca informações na base de conhecimento",
        {
            "Query": "depilação laser preço",
            "Categoria": "Tratamentos",
            "Resultados": "3 artigos encontrados",
            "Relevância": "Alta"
        }
    )
    
    system.log(
        "🧠 LLM CALL (Grok)",
        "Processa pergunta e gera resposta",
        {
            "Provider": "xAI Grok-4-Reasoning",
            "Tokens": "~500 tokens",
            "Custo": "$0.002",
            "Tempo": "1.2s",
            "Confiança": "high"
        }
    )
    
    system.log(
        "💾 REDIS - CACHE SET",
        "Armazena resposta no cache (high confidence)",
        {
            "Cache Key": "faq_cache:a1b2c3d4e5f6...",
            "TTL": "3600s (1 hora)",
            "Tamanho": "~2KB",
            "Status": "Cached"
        }
    )
    
    system.log(
        "💾 REDIS - CONTEXTO UPDATE",
        "Atualiza histórico de conversação",
        {
            "Key": "conv:12345",
            "Mensagens": "2 (user + assistant)",
            "TTL": "24 horas"
        }
    )
    
    system.log(
        "📤 RESPOSTA ENVIADA",
        "Sistema envia resposta via Chatwoot",
        {
            "Para": "Maria Silva",
            "Resposta": """Olá Maria! 😊

A depilação a laser tem valores que variam conforme a região:

💙 Áreas pequenas (buço, axilas): R$ 150-250/sessão
💙 Áreas médias (virilha, pernas): R$ 300-500/sessão
💙 Áreas grandes (corpo todo): Pacotes a partir de R$ 2.500

Oferecemos avaliação GRATUITA para definir o melhor plano! 

Gostaria de agendar uma avaliação? 📅""",
            "Tempo Total": "1.5s"
        }
    )
    
    await asyncio.sleep(2)
    
    # ========================================================================
    # INTERAÇÃO 2: Mesma pergunta (CACHE HIT)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("INTERAÇÃO 2: Mesma Pergunta (Demonstra Cache)")
    print("=" * 80)
    
    system.log(
        "📱 MENSAGEM RECEBIDA",
        "Outro paciente faz a mesma pergunta",
        {
            "De": "João Santos (+55 11 91234-5678)",
            "Mensagem": "Quanto custa depilação a laser?",
            "Timestamp": "14:35:20"
        }
    )
    
    system.log(
        "🤖 SUPERVISOR AGENT",
        "Classifica intenção",
        {
            "Intenção": "FAQ",
            "Agente": "FAQ Agent"
        }
    )
    
    system.log(
        "💾 REDIS - FAQ CACHE",
        "FAQ Agent verifica cache",
        {
            "Pergunta": "Quanto custa depilação a laser?",
            "Normalizada": "preço depilação laser",
            "Cache Key": "faq_cache:a1b2c3d4e5f6...",
            "Resultado": "✅ HIT! (resposta encontrada)",
            "Hit Rate": "50%",
            "Tempo": "<10ms"
        }
    )
    
    system.log(
        "⚡ CACHE HIT",
        "Resposta servida diretamente do cache",
        {
            "LLM Call": "❌ NÃO (economizado)",
            "Custo": "$0.000 (vs $0.002)",
            "Tempo": "0.01s (vs 1.2s)",
            "Economia": "100% custo, 99% tempo"
        }
    )
    
    system.log(
        "📤 RESPOSTA ENVIADA",
        "Mesma resposta, mas instantânea",
        {
            "Para": "João Santos",
            "Fonte": "Redis Cache",
            "Tempo Total": "0.05s (30x mais rápido!)"
        }
    )
    
    await asyncio.sleep(2)
    
    # ========================================================================
    # INTERAÇÃO 3: Agendamento (SCHEDULER)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("INTERAÇÃO 3: Agendamento de Consulta")
    print("=" * 80)
    
    system.log(
        "📱 MENSAGEM RECEBIDA",
        "Maria quer agendar",
        {
            "De": "Maria Silva",
            "Mensagem": "Sim, quero agendar a avaliação!",
            "Timestamp": "14:36:00"
        }
    )
    
    system.log(
        "🔍 REDIS - CONTEXTO",
        "Recupera histórico da conversa",
        {
            "Key": "conv:12345",
            "Mensagens": "4 mensagens",
            "Contexto": "Paciente perguntou sobre depilação laser"
        }
    )
    
    system.log(
        "🤖 SUPERVISOR AGENT",
        "Classifica intenção com contexto",
        {
            "Entrada": "Sim, quero agendar a avaliação!",
            "Contexto": "Conversa sobre depilação laser",
            "Intenção": "SCHEDULING",
            "Agente": "Scheduler Agent"
        }
    )
    
    system.log(
        "👤 INTAKE AGENT",
        "Verifica informações de contato",
        {
            "Telefone": "+55 11 98765-4321",
            "Status": "Contato não cadastrado",
            "Ação": "Solicitar informações"
        }
    )
    
    system.log(
        "📤 RESPOSTA ENVIADA",
        "Solicita informações para cadastro",
        {
            "Mensagem": """Ótimo! Para agendar sua avaliação, preciso de algumas informações:

📝 Qual seu nome completo?
📧 Qual seu e-mail?
📅 Qual sua data de nascimento?"""
        }
    )
    
    await asyncio.sleep(2)
    
    # ========================================================================
    # INTERAÇÃO 4: Fornece informações
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("INTERAÇÃO 4: Cadastro de Informações")
    print("=" * 80)
    
    system.log(
        "📱 MENSAGEM RECEBIDA",
        "Maria fornece informações",
        {
            "Mensagem": """Maria Silva Santos
maria.silva@email.com
15/03/1990"""
        }
    )
    
    system.log(
        "👤 INTAKE AGENT",
        "Processa e valida informações",
        {
            "Nome": "Maria Silva Santos",
            "Email": "maria.silva@email.com",
            "Data Nascimento": "15/03/1990",
            "Validação": "✅ Todos os campos válidos"
        }
    )
    
    system.log(
        "💾 SUPABASE",
        "Cria registro de contato",
        {
            "Tabela": "contacts",
            "ID": "uuid-12345",
            "Nome": "Maria Silva Santos",
            "Telefone": "+55 11 98765-4321",
            "Email": "maria.silva@email.com",
            "Status": "Criado com sucesso"
        }
    )
    
    system.log(
        "📅 SCHEDULER AGENT",
        "Busca horários disponíveis",
        {
            "API": "Calendar API",
            "Serviço": "Avaliação Gratuita",
            "Período": "Próximos 7 dias",
            "Horários": "15 slots disponíveis"
        }
    )
    
    system.log(
        "📤 RESPOSTA ENVIADA",
        "Apresenta opções de horário",
        {
            "Mensagem": """Perfeito, Maria! Cadastro realizado ✅

Horários disponíveis para avaliação:

📅 Amanhã (17/10):
• 09:00
• 14:00
• 16:30

📅 Sexta (18/10):
• 10:00
• 15:00

Qual horário prefere?"""
        }
    )
    
    await asyncio.sleep(2)
    
    # ========================================================================
    # INTERAÇÃO 5: Confirmação de agendamento
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("INTERAÇÃO 5: Confirmação de Agendamento")
    print("=" * 80)
    
    system.log(
        "📱 MENSAGEM RECEBIDA",
        "Maria escolhe horário",
        {
            "Mensagem": "Amanhã às 14:00 por favor"
        }
    )
    
    system.log(
        "📅 SCHEDULER AGENT",
        "Cria agendamento",
        {
            "API Call": "POST /api/bookings",
            "Data": "2025-10-17",
            "Horário": "14:00",
            "Serviço": "Avaliação Gratuita",
            "Duração": "30 minutos"
        }
    )
    
    system.log(
        "💾 SUPABASE",
        "Registra agendamento",
        {
            "Tabela": "appointments",
            "ID": "uuid-67890",
            "Contact ID": "uuid-12345",
            "Status": "confirmed",
            "Reminder": "Agendado para D-1 e H-2"
        }
    )
    
    system.log(
        "📤 RESPOSTA ENVIADA",
        "Confirmação com detalhes",
        {
            "Mensagem": """✅ Agendamento confirmado!

📅 Data: 17/10/2025 (Amanhã)
⏰ Horário: 14:00
📍 Local: Clínica Luana - Rua das Flores, 123
⏱️ Duração: 30 minutos

Você receberá lembretes:
• 1 dia antes
• 2 horas antes

Precisa reagendar? É só avisar com 4h de antecedência.

Até amanhã, Maria! 💙"""
        }
    )
    
    await asyncio.sleep(2)
    
    # ========================================================================
    # ESTATÍSTICAS FINAIS
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS DO ATENDIMENTO")
    print("=" * 80)
    
    system.log(
        "📊 MÉTRICAS GERAIS",
        "Resumo do atendimento",
        {
            "Total de Mensagens": "10 (5 do paciente, 5 do sistema)",
            "Tempo Total": "~6 minutos",
            "Agentes Utilizados": "Supervisor, FAQ, Intake, Scheduler",
            "Resultado": "✅ Agendamento confirmado"
        }
    )
    
    system.log(
        "💾 REDIS - CACHE STATS",
        "Performance do cache",
        {
            "FAQ Cache Hits": "1",
            "FAQ Cache Misses": "1",
            "Hit Rate": "50%",
            "Economia LLM": "$0.002",
            "Economia Tempo": "1.15s",
            "Contexto Armazenado": "10 mensagens (conv:12345)"
        }
    )
    
    system.log(
        "💰 CUSTOS",
        "Análise de custos",
        {
            "LLM Calls": "4 (Supervisor: 2, FAQ: 1, Scheduler: 1)",
            "Custo Total": "$0.008",
            "Custo com Cache": "$0.008",
            "Custo sem Cache": "$0.010",
            "Economia": "20%"
        }
    )
    
    system.log(
        "⚡ PERFORMANCE",
        "Tempos de resposta",
        {
            "Resposta Média": "0.8s",
            "Resposta Cached": "0.05s",
            "Resposta LLM": "1.2s",
            "Melhoria Cache": "24x mais rápido"
        }
    )
    
    system.log(
        "🎯 PRÓXIMOS PASSOS",
        "Ações automáticas agendadas",
        {
            "D-1 (16/10 14:00)": "Lembrete via WhatsApp",
            "H-2 (17/10 12:00)": "Lembrete via WhatsApp",
            "Pós-atendimento": "Feedback automático (se configurado)"
        }
    )
    
    print("\n" + "=" * 80)
    print("FIM DO EXEMPLO")
    print("=" * 80)
    
    print("\n📝 RESUMO:")
    print("  • Paciente fez pergunta sobre preço (FAQ)")
    print("  • Sistema usou cache Redis para otimizar")
    print("  • Paciente decidiu agendar (Scheduler)")
    print("  • Sistema coletou informações (Intake)")
    print("  • Agendamento confirmado com sucesso")
    print("  • Lembretes automáticos configurados")
    print("\n✅ Atendimento completo e eficiente!")


if __name__ == "__main__":
    asyncio.run(exemplo_atendimento_completo())
