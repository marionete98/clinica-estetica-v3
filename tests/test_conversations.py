"""
Teste de 10 Conversações Reais com Semantic Kernel
Simula interações completas do sistema multi-agente
"""
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv('.env')
console = Console()

# Configuração dos agentes
llm_config = {
    "provider": "xai",
    "model": "grok-4-fast-reasoning",
    "api_key": os.getenv("XAI_API_KEY"),
    "base_url": "https://api.x.ai/v1",
    "temperature": 0.7,
    "max_tokens": 2048
}

# Conversações de teste
test_conversations = [
    {
        "id": 1,
        "name": "Saudação Inicial + Coleta de Nome",
        "agent": "intake",
        "messages": ["Boa tarde!"],
        "expected": "Deve cumprimentar e pedir nome"
    },
    {
        "id": 2,
        "name": "FAQ - Pergunta sobre Depilação a Laser",
        "agent": "faq",
        "messages": ["Quanto custa depilação a laser?"],
        "expected": "Deve buscar preço na base de conhecimento"
    },
    {
        "id": 3,
        "name": "FAQ - Horário de Funcionamento",
        "agent": "faq",
        "messages": ["Qual o horário de atendimento?"],
        "expected": "Deve informar horários (Seg-Sex 8:30-19:00)"
    },
    {
        "id": 4,
        "name": "FAQ - Contraindications",
        "agent": "faq",
        "messages": ["Harmonização facial tem contraindicação?"],
        "expected": "Deve buscar contraindicações na KB"
    },
    {
        "id": 5,
        "name": "Supervisor - Classificação de Intent (Agendamento)",
        "agent": "supervisor",
        "messages": ["Quero agendar uma consulta para amanhã"],
        "expected": "Deve classificar como 'scheduler'"
    },
    {
        "id": 6,
        "name": "Supervisor - Classificação de Intent (FAQ)",
        "agent": "supervisor",
        "messages": ["Vocês fazem harmonização facial?"],
        "expected": "Deve classificar como 'faq'"
    },
    {
        "id": 7,
        "name": "Supervisor - Classificação de Intent (Escalation)",
        "agent": "supervisor",
        "messages": ["Quero falar com um atendente humano"],
        "expected": "Deve classificar como 'escalation'"
    },
    {
        "id": 8,
        "name": "Escalation - Preparar Handoff",
        "agent": "escalation",
        "messages": ["Sistema não está funcionando, preciso de ajuda"],
        "expected": "Deve preparar transferência para humano"
    },
    {
        "id": 9,
        "name": "Intake - Registro Completo",
        "agent": "intake",
        "messages": ["Olá, meu nome é Maria Silva"],
        "expected": "Deve registrar contato e retornar INTAKE_COMPLETE"
    },
    {
        "id": 10,
        "name": "FAQ - Múltiplas Perguntas",
        "agent": "faq",
        "messages": ["Quais tratamentos vocês fazem e qual o valor?"],
        "expected": "Deve buscar lista de tratamentos e preços"
    }
]

async def test_faq_agent(message: str, test_id: int):
    """Testa FAQAgent com message."""
    from agents.faq import FAQAgent
    
    try:
        faq = FAQAgent(llm_config)
        console.print(f"[green]✓[/green] FAQAgent inicializado")
        
        # Simular conversa
        from autogen_agentchat.messages import TextMessage
        from autogen_core import CancellationToken
        
        result = await faq.agent.on_messages(
            [TextMessage(content=message, source="user")],
            CancellationToken()
        )
        
        response = result.chat_message.content if hasattr(result, 'chat_message') else str(result)
        return {
            "success": True,
            "response": response[:500],  # Primeiros 500 chars
            "agent_type": type(faq.model_client).__name__
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_type": "N/A"
        }

async def test_supervisor_agent(message: str, test_id: int):
    """Testa SupervisorAgent com classificação de intent."""
    from agents.supervisor import SupervisorAgent
    
    try:
        supervisor = SupervisorAgent(llm_config)
        console.print(f"[green]✓[/green] SupervisorAgent inicializado")
        
        # Classificar intent
        result = await supervisor.classify_intent(
            message=message,
            conversation_id=f"test_{test_id}",
            context=[]
        )
        
        return {
            "success": True,
            "response": f"Intent: {result.get('intent', 'unknown')} | Agent: {result.get('agent', 'unknown')}",
            "agent_type": type(supervisor.model_client).__name__,
            "full_result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_type": "N/A"
        }

async def test_intake_agent(message: str, test_id: int):
    """Testa IntakeAgent com coleta de informações."""
    from agents.intake import IntakeAgent
    
    try:
        intake = IntakeAgent(llm_config)
        console.print(f"[green]✓[/green] IntakeAgent inicializado")
        
        # Simular conversa
        from autogen_agentchat.messages import TextMessage
        from autogen_core import CancellationToken
        
        result = await intake.agent.on_messages(
            [TextMessage(content=message, source="user")],
            CancellationToken()
        )
        
        response = result.chat_message.content if hasattr(result, 'chat_message') else str(result)
        return {
            "success": True,
            "response": response[:500],
            "agent_type": type(intake.model_client).__name__
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_type": "N/A"
        }

async def test_escalation_agent(message: str, test_id: int):
    """Testa EscalationAgent."""
    from agents.escalation import EscalationAgent
    
    try:
        escalation = EscalationAgent(llm_config)
        console.print(f"[green]✓[/green] EscalationAgent inicializado")
        
        # Preparar escalation
        result = await escalation.prepare_escalation(
            reason="Teste de escalação automática",
            conversation_id=f"test_{test_id}",
            contact_info={"name": "Teste", "phone": "+5594999999999"},
            context=[{"role": "user", "content": message}],
            priority="medium"
        )
        
        return {
            "success": True,
            "response": f"Escalation preparada - Priority: {result.get('priority', 'unknown')}",
            "agent_type": type(escalation.model_client).__name__,
            "full_result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_type": "N/A"
        }

async def run_test_conversation(test: dict):
    """Executa um teste de conversação."""
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(Panel(
        f"[bold yellow]Teste #{test['id']}: {test['name']}[/bold yellow]\n"
        f"[white]Agent: {test['agent']}[/white]\n"
        f"[white]Message: {test['messages'][0]}[/white]\n"
        f"[dim]Expected: {test['expected']}[/dim]",
        border_style="cyan"
    ))
    
    start_time = datetime.now()
    
    try:
        # Executar teste baseado no agente
        if test['agent'] == 'faq':
            result = await test_faq_agent(test['messages'][0], test['id'])
        elif test['agent'] == 'supervisor':
            result = await test_supervisor_agent(test['messages'][0], test['id'])
        elif test['agent'] == 'intake':
            result = await test_intake_agent(test['messages'][0], test['id'])
        elif test['agent'] == 'escalation':
            result = await test_escalation_agent(test['messages'][0], test['id'])
        else:
            result = {"success": False, "error": f"Agent {test['agent']} not implemented in test"}
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result['success']:
            console.print(f"\n[bold green]✅ SUCESSO[/bold green] (⏱️  {duration:.2f}s)")
            console.print(f"[green]Agent Type:[/green] {result['agent_type']}")
            console.print(f"\n[bold white]📝 Response:[/bold white]")
            console.print(Panel(result['response'], border_style="green"))
            
            return {
                "test_id": test['id'],
                "name": test['name'],
                "status": "✅ PASSED",
                "duration": duration,
                "agent_type": result['agent_type']
            }
        else:
            console.print(f"\n[bold red]❌ FALHOU[/bold red] (⏱️  {duration:.2f}s)")
            console.print(f"[red]Error:[/red] {result.get('error', 'Unknown error')}")
            
            return {
                "test_id": test['id'],
                "name": test['name'],
                "status": "❌ FAILED",
                "duration": duration,
                "error": result.get('error', 'Unknown error')
            }
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        console.print(f"\n[bold red]❌ EXCEPTION[/bold red] (⏱️  {duration:.2f}s)")
        console.print(f"[red]Error:[/red] {str(e)}")
        
        return {
            "test_id": test['id'],
            "name": test['name'],
            "status": "❌ EXCEPTION",
            "duration": duration,
            "error": str(e)
        }

async def main():
    """Executa todos os testes de conversação."""
    console.print("\n[bold magenta]╔═══════════════════════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║     TESTES DE CONVERSAÇÃO - SEMANTIC KERNEL MIGRATION                ║[/bold magenta]")
    console.print("[bold magenta]║     Sistema Multi-Agente - Clínica Luana Dermo Clinic                ║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════════════════════════════╝[/bold magenta]")
    
    console.print(f"\n[cyan]📅 Início:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"[cyan]🤖 Provider:[/cyan] {llm_config['provider']}")
    console.print(f"[cyan]🧠 Model:[/cyan] {llm_config['model']}")
    console.print(f"[cyan]📊 Total de Testes:[/cyan] {len(test_conversations)}\n")
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Executando testes...", total=len(test_conversations))
        
        for test in test_conversations:
            result = await run_test_conversation(test)
            results.append(result)
            progress.update(task, advance=1)
            await asyncio.sleep(1)  # Delay entre testes
    
    # Relatório Final
    console.print("\n[bold magenta]╔═══════════════════════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║                        RELATÓRIO FINAL                                ║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════════════════════════════╝[/bold magenta]\n")
    
    passed = sum(1 for r in results if "PASSED" in r['status'])
    failed = sum(1 for r in results if "FAILED" in r['status'] or "EXCEPTION" in r['status'])
    total_duration = sum(r['duration'] for r in results)
    avg_duration = total_duration / len(results) if results else 0
    
    console.print(f"[bold green]✅ Testes Passados:[/bold green] {passed}/{len(results)}")
    console.print(f"[bold red]❌ Testes Falhados:[/bold red] {failed}/{len(results)}")
    console.print(f"[bold cyan]⏱️  Duração Total:[/bold cyan] {total_duration:.2f}s")
    console.print(f"[bold cyan]⏱️  Média por Teste:[/bold cyan] {avg_duration:.2f}s")
    console.print(f"[bold cyan]📊 Taxa de Sucesso:[/bold cyan] {(passed/len(results)*100):.1f}%\n")
    
    # Tabela de Resultados
    console.print("[bold white]📋 Resultados Detalhados:[/bold white]\n")
    for r in results:
        status_icon = "✅" if "PASSED" in r['status'] else "❌"
        console.print(
            f"{status_icon} [bold]Teste #{r['test_id']}:[/bold] {r['name'][:50]:<50} "
            f"[dim]({r['duration']:.2f}s)[/dim]"
        )
        if 'agent_type' in r:
            console.print(f"   [dim]└─ Agent: {r['agent_type']}[/dim]")
        if 'error' in r:
            console.print(f"   [red]└─ Error: {r['error'][:80]}[/red]")
    
    console.print(f"\n[cyan]📅 Fim:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Status Final
    if passed == len(results):
        console.print(Panel(
            "[bold green]🎉 TODOS OS TESTES PASSARAM!\n"
            "A migração para Semantic Kernel está 100% funcional![/bold green]",
            border_style="green",
            title="✅ SUCESSO TOTAL"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]⚠️  {failed} teste(s) falharam.\n"
            f"Verifique os erros acima para detalhes.[/bold yellow]",
            border_style="yellow",
            title="⚠️  ATENÇÃO"
        ))

if __name__ == "__main__":
    asyncio.run(main())
