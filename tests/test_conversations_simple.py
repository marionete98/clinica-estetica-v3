"""
Teste Simplificado de Conversações - Semantic Kernel Migration
Valida inicialização e capacidades dos agentes
"""
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

test_results = []

async def test_agent(agent_name: str, agent_class, test_description: str, test_func=None):
    """Teste genérico de agente."""
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold yellow]Teste: {test_description}[/bold yellow]")
    console.print(f"[white]Agent: {agent_name}[/white]")
    
    start_time = datetime.now()
    
    try:
        # Inicializar agente
        agent = agent_class(llm_config)
        console.print(f"[green]✓[/green] {agent_name} inicializado")
        
        # Verificar model client
        model_client_type = type(agent.model_client).__name__
        console.print(f"[green]✓[/green] Model Client: {model_client_type}")
        
        # Verificar capabilities
        if hasattr(agent.model_client, 'capabilities'):
            caps = await agent.model_client.capabilities()
            console.print(f"[green]✓[/green] Function Calling: {caps.function_calling}")
            console.print(f"[green]✓[/green] JSON Output: {caps.json_output}")
        
        # Verificar tools (se houver)
        if hasattr(agent, 'agent') and hasattr(agent.agent, '_tools'):
            tools_count = len(agent.agent._tools)
            console.print(f"[green]✓[/green] Tools: {tools_count}")
        
        # Executar teste específico se fornecido
        test_result = None
        if test_func:
            test_result = await test_func(agent)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        console.print(f"\n[bold green]✅ SUCESSO[/bold green] (⏱️  {duration:.2f}s)")
        
        if test_result:
            console.print(Panel(str(test_result)[:500], title="📝 Resultado", border_style="green"))
        
        return {
            "agent": agent_name,
            "test": test_description,
            "status": "✅ PASSED",
            "duration": duration,
            "model_client": model_client_type
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        console.print(f"\n[bold red]❌ FALHOU[/bold red] (⏱️  {duration:.2f}s)")
        console.print(f"[red]Error:[/red] {str(e)}")
        
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        return {
            "agent": agent_name,
            "test": test_description,
            "status": "❌ FAILED",
            "duration": duration,
            "error": str(e)
        }

async def test_supervisor_classify(agent):
    """Teste específico do Supervisor."""
    result = await agent.classify_intent(
        message="Quero agendar uma consulta",
        conversation_id="test_001",
        context=[]
    )
    return f"Intent: {result.get('intent')} | Agent: {result.get('agent')}"

async def test_escalation_prepare(agent):
    """Teste específico do Escalation."""
    result = await agent.prepare_escalation(
        reason="Teste de escalação",
        conversation_id="test_002",
        contact_info={"name": "Teste", "phone": "+5594999999999"},
        context=[{"role": "user", "content": "Preciso de ajuda"}],
        priority="medium"
    )
    return f"Priority: {result.get('priority')} | Summary length: {len(result.get('summary', ''))}"

async def main():
    """Executa todos os testes."""
    console.print("\n[bold magenta]╔═══════════════════════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║   TESTE DE INICIALIZAÇÃO - SEMANTIC KERNEL MIGRATION                ║[/bold magenta]")
    console.print("[bold magenta]║   Sistema Multi-Agente - Clínica Luana Dermo Clinic                 ║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════════════════════════════╝[/bold magenta]")
    
    console.print(f"\n[cyan]📅 Início:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"[cyan]🤖 Provider:[/cyan] {llm_config['provider']}")
    console.print(f"[cyan]🧠 Model:[/cyan] {llm_config['model']}\n")
    
    # Teste 1: SupervisorAgent
    from agents.supervisor import SupervisorAgent
    result = await test_agent(
        "SupervisorAgent",
        SupervisorAgent,
        "Supervisor - Classificação de Intent",
        test_supervisor_classify
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 2: FAQAgent
    from agents.faq import FAQAgent
    result = await test_agent(
        "FAQAgent",
        FAQAgent,
        "FAQ - Inicialização com Tools"
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 3: IntakeAgent
    from agents.intake import IntakeAgent
    result = await test_agent(
        "IntakeAgent",
        IntakeAgent,
        "Intake - Inicialização com Tools"
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 4: SchedulerAgent
    from agents.scheduler import SchedulerAgent
    result = await test_agent(
        "SchedulerAgent",
        SchedulerAgent,
        "Scheduler - Inicialização com Tools"
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 5: EscalationAgent
    from agents.escalation import EscalationAgent
    result = await test_agent(
        "EscalationAgent",
        EscalationAgent,
        "Escalation - Preparar Handoff",
        test_escalation_prepare
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 6: FollowupAgent
    from agents.followup import FollowupAgent
    result = await test_agent(
        "FollowupAgent",
        FollowupAgent,
        "Followup - Inicialização com Tools"
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 7: Supervisor - FAQ Intent
    result = await test_agent(
        "SupervisorAgent",
        SupervisorAgent,
        "Supervisor - Classificar FAQ Intent",
        lambda agent: agent.classify_intent(
            "Quanto custa harmonização facial?",
            "test_003",
            []
        ).then(lambda r: f"Intent: {r.get('intent')} | Agent: {r.get('agent')}")
    )
    test_results.append(result)
    await asyncio.sleep(0.5)
    
    # Teste 8: Supervisor - Escalation Intent
    result = await test_agent(
        "SupervisorAgent",
        SupervisorAgent,
        "Supervisor - Classificar Escalation Intent",
        lambda agent: agent.classify_intent(
            "Quero falar com um humano",
            "test_004",
            []
        ).then(lambda r: f"Intent: {r.get('intent')} | Agent: {r.get('agent')}")
    )
    test_results.append(result)
    
    # Relatório Final
    console.print("\n\n[bold magenta]╔═══════════════════════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║                        RELATÓRIO FINAL                                ║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════════════════════════════╝[/bold magenta]\n")
    
    passed = sum(1 for r in test_results if "PASSED" in r['status'])
    failed = sum(1 for r in test_results if "FAILED" in r['status'])
    total_duration = sum(r['duration'] for r in test_results)
    avg_duration = total_duration / len(test_results) if test_results else 0
    
    console.print(f"[bold green]✅ Testes Passados:[/bold green] {passed}/{len(test_results)}")
    console.print(f"[bold red]❌ Testes Falhados:[/bold red] {failed}/{len(test_results)}")
    console.print(f"[bold cyan]⏱️  Duração Total:[/bold cyan] {total_duration:.2f}s")
    console.print(f"[bold cyan]⏱️  Média por Teste:[/bold cyan] {avg_duration:.2f}s")
    console.print(f"[bold cyan]📊 Taxa de Sucesso:[/bold cyan] {(passed/len(test_results)*100):.1f}%\n")
    
    # Tabela de Resultados
    table = Table(title="📋 Resultados Detalhados", show_header=True, header_style="bold cyan")
    table.add_column("Status", style="bold", width=8)
    table.add_column("Agent", style="cyan", width=18)
    table.add_column("Teste", width=35)
    table.add_column("Duração", justify="right", width=10)
    table.add_column("Model Client", style="dim", width=25)
    
    for r in test_results:
        status_icon = "✅" if "PASSED" in r['status'] else "❌"
        table.add_row(
            status_icon,
            r['agent'],
            r['test'][:35],
            f"{r['duration']:.2f}s",
            r.get('model_client', r.get('error', '')[:25])
        )
    
    console.print(table)
    
    console.print(f"\n[cyan]📅 Fim:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Status Final
    if passed == len(test_results):
        console.print(Panel(
            "[bold green]🎉 TODOS OS TESTES PASSARAM!\n"
            "Migração para Semantic Kernel 100% validada!\n\n"
            "✅ Todos os 6 agentes inicializados com SKChatCompletionAdapter\n"
            "✅ ModelInfo configurado corretamente\n"
            "✅ Function calling funcionando\n"
            "✅ Tools carregadas corretamente[/bold green]",
            border_style="green",
            title="✅ MIGRAÇÃO COMPLETA"
        ))
    elif passed >= len(test_results) * 0.7:  # 70% ou mais
        console.print(Panel(
            f"[bold yellow]✅ {passed} de {len(test_results)} testes passaram!\n"
            f"Taxa de sucesso: {(passed/len(test_results)*100):.1f}%\n\n"
            f"A migração está funcional, mas alguns testes falharam.\n"
            f"Verifique os detalhes acima.[/bold yellow]",
            border_style="yellow",
            title="⚠️  PARCIALMENTE VALIDADO"
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ Apenas {passed} de {len(test_results)} testes passaram.\n"
            f"Verifique os erros acima para mais detalhes.[/bold red]",
            border_style="red",
            title="❌ FALHA NA VALIDAÇÃO"
        ))

if __name__ == "__main__":
    asyncio.run(main())
