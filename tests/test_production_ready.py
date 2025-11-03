"""
✅ TESTE DE PRONTIDÃO PARA PRODUÇÃO - RAILWAY DEPLOY
Valida que o sistema está 100% pronto para deploy
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

load_dotenv('.env')
console = Console()

# Configurações
llm_config = {
    "provider": "xai",
    "model": "grok-4-fast-reasoning",
    "api_key": os.getenv("XAI_API_KEY"),
    "base_url": "https://api.x.ai/v1",
    "temperature": 0.7,
    "max_tokens": 2048
}

test_results = []

def test_result(name: str, status: bool, message: str = "", duration: float = 0):
    """Registra resultado de teste."""
    test_results.append({
        "name": name,
        "status": "✅ PASSOU" if status else "❌ FALHOU",
        "message": message,
        "duration": duration
    })
    
    if status:
        console.print(f"[green]✅ {name}[/green]", end="")
        if message:
            console.print(f" - [dim]{message}[/dim]")
        else:
            console.print()
    else:
        console.print(f"[red]❌ {name}[/red]")
        if message:
            console.print(f"   [red]└─ {message}[/red]")

def check_env_vars():
    """Verifica variáveis de ambiente necessárias."""
    console.print("\n[bold cyan]1️⃣ Verificando Variáveis de Ambiente...[/bold cyan]")
    
    required_vars = [
        "XAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "REDIS_URL",
        "CHATWOOT_API_URL",
        "CHATWOOT_ACCOUNT_ID",
        "CHATWOOT_API_TOKEN"
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked = f"***{value[-10:]}" if len(value) > 10 else "***"
            test_result(f"ENV: {var}", True, masked)
        else:
            test_result(f"ENV: {var}", False, "Variável não configurada")
            all_ok = False
    
    return all_ok

def check_dependencies():
    """Verifica dependências instaladas."""
    console.print("\n[bold cyan]2️⃣ Verificando Dependências...[/bold cyan]")
    
    dependencies = [
        ("autogen-agentchat", "autogen_agentchat"),
        ("autogen-core", "autogen_core"),
        ("autogen-ext", "autogen_ext"),
        ("semantic-kernel", "semantic_kernel"),
        ("google-generativeai", "google.generativeai"),
        ("openai", "openai"),
        ("fastapi", "fastapi"),
        ("supabase", "supabase"),
        ("redis", "redis"),
    ]
    
    all_ok = True
    for name, module in dependencies:
        try:
            __import__(module)
            test_result(f"DEP: {name}", True)
        except ImportError as e:
            test_result(f"DEP: {name}", False, str(e))
            all_ok = False
    
    return all_ok

def check_agent_files():
    """Verifica que todos os arquivos de agentes existem."""
    console.print("\n[bold cyan]3️⃣ Verificando Arquivos dos Agentes...[/bold cyan]")
    
    agent_files = [
        "agents/supervisor.py",
        "agents/faq.py",
        "agents/intake.py",
        "agents/scheduler.py",
        "agents/escalation.py",
        "agents/followup.py"
    ]
    
    all_ok = True
    for file in agent_files:
        if os.path.exists(file):
            # Verificar se tem SKChatCompletionAdapter
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'SKChatCompletionAdapter' in content:
                    test_result(f"FILE: {file}", True, "com SKChatCompletionAdapter")
                else:
                    test_result(f"FILE: {file}", False, "sem SKChatCompletionAdapter")
                    all_ok = False
        else:
            test_result(f"FILE: {file}", False, "Arquivo não encontrado")
            all_ok = False
    
    return all_ok

async def check_agent_initialization():
    """Testa inicialização de todos os agentes."""
    console.print("\n[bold cyan]4️⃣ Testando Inicialização dos Agentes...[/bold cyan]")
    
    agents = [
        ("SupervisorAgent", "agents.supervisor", "SupervisorAgent"),
        ("FAQAgent", "agents.faq", "FAQAgent"),
        ("IntakeAgent", "agents.intake", "IntakeAgent"),
        ("SchedulerAgent", "agents.scheduler", "SchedulerAgent"),
        ("EscalationAgent", "agents.escalation", "EscalationAgent"),
        ("FollowupAgent", "agents.followup", "FollowupAgent"),
    ]
    
    all_ok = True
    for agent_name, module_name, class_name in agents:
        try:
            start = datetime.now()
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent = agent_class(llm_config)
            duration = (datetime.now() - start).total_seconds()
            
            # Verificar model_client
            if hasattr(agent, 'model_client'):
                client_type = type(agent.model_client).__name__
                if client_type == 'SKChatCompletionAdapter':
                    test_result(
                        f"AGENT: {agent_name}",
                        True,
                        f"SKChatCompletionAdapter ({duration:.2f}s)",
                        duration
                    )
                else:
                    test_result(
                        f"AGENT: {agent_name}",
                        False,
                        f"Tipo errado: {client_type}",
                        duration
                    )
                    all_ok = False
            else:
                test_result(f"AGENT: {agent_name}", False, "Sem model_client", duration)
                all_ok = False
                
        except Exception as e:
            test_result(f"AGENT: {agent_name}", False, str(e)[:80])
            all_ok = False
    
    return all_ok

async def check_supervisor_classification():
    """Testa classificação de intents do Supervisor."""
    console.print("\n[bold cyan]5️⃣ Testando Classificação de Intents...[/bold cyan]")
    
    from agents.supervisor import SupervisorAgent
    
    test_cases = [
        ("Quero agendar consulta", "scheduler"),
        ("Quanto custa depilação?", "faq"),
        ("Quero falar com humano", "escalation"),
    ]
    
    all_ok = True
    try:
        supervisor = SupervisorAgent(llm_config)
        
        for message, expected_agent in test_cases:
            try:
                start = datetime.now()
                result = await supervisor.classify_intent(
                    message=message,
                    conversation_id="test_001",
                    context=[]
                )
                duration = (datetime.now() - start).total_seconds()
                
                returned_agent = result.get('agent', '')
                if returned_agent == expected_agent:
                    test_result(
                        f"INTENT: '{message[:30]}...'",
                        True,
                        f"→ {returned_agent} ({duration:.2f}s)",
                        duration
                    )
                else:
                    test_result(
                        f"INTENT: '{message[:30]}...'",
                        False,
                        f"Esperado {expected_agent}, retornou {returned_agent}",
                        duration
                    )
                    all_ok = False
                    
            except Exception as e:
                test_result(f"INTENT: '{message[:30]}...'", False, str(e)[:80])
                all_ok = False
                
    except Exception as e:
        test_result("SUPERVISOR", False, f"Erro ao inicializar: {str(e)[:80]}")
        all_ok = False
    
    return all_ok

async def check_escalation_preparation():
    """Testa preparação de escalation."""
    console.print("\n[bold cyan]6️⃣ Testando Escalation Agent...[/bold cyan]")
    
    from agents.escalation import EscalationAgent
    
    try:
        start = datetime.now()
        escalation = EscalationAgent(llm_config)
        
        result = await escalation.prepare_escalation(
            reason="Teste de prontidão",
            conversation_id="test_002",
            contact_info={"name": "Teste", "phone": "+5594999999999"},
            context=[{"role": "user", "content": "Preciso de ajuda"}],
            priority="medium"
        )
        duration = (datetime.now() - start).total_seconds()
        
        if result and 'priority' in result:
            test_result(
                "ESCALATION: prepare_escalation",
                True,
                f"Priority: {result['priority']} ({duration:.2f}s)",
                duration
            )
            return True
        else:
            test_result("ESCALATION: prepare_escalation", False, "Resposta inválida")
            return False
            
    except Exception as e:
        test_result("ESCALATION", False, str(e)[:80])
        return False

def check_requirements():
    """Verifica requirements.txt."""
    console.print("\n[bold cyan]7️⃣ Verificando Requirements.txt...[/bold cyan]")
    
    if not os.path.exists('requirements.txt'):
        test_result("requirements.txt", False, "Arquivo não encontrado")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = [
        ('autogen-agentchat', 'autogen-agentchat'),
        ('autogen-core', 'autogen-core'),
        ('autogen-ext', 'autogen-ext.*semantic-kernel'),
        ('semantic-kernel', 'semantic-kernel'),
        ('google-generativeai', 'google-generativeai'),
    ]
    
    all_ok = True
    for name, pattern in required_packages:
        import re
        if re.search(pattern, content):
            test_result(f"REQ: {name}", True)
        else:
            test_result(f"REQ: {name}", False, "Não encontrado em requirements.txt")
            all_ok = False
    
    return all_ok

def generate_report():
    """Gera relatório final."""
    console.print("\n\n[bold magenta]" + "="*80 + "[/bold magenta]")
    console.print("[bold magenta]                        RELATÓRIO FINAL DE PRONTIDÃO[/bold magenta]")
    console.print("[bold magenta]" + "="*80 + "[/bold magenta]\n")
    
    passed = sum(1 for r in test_results if "PASSOU" in r['status'])
    failed = sum(1 for r in test_results if "FALHOU" in r['status'])
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    # Estatísticas
    console.print(f"[bold white]📊 Estatísticas:[/bold white]")
    console.print(f"   ✅ Testes Passados: [green]{passed}[/green]")
    console.print(f"   ❌ Testes Falhados: [red]{failed}[/red]")
    console.print(f"   📈 Taxa de Sucesso: [cyan]{success_rate:.1f}%[/cyan]")
    console.print(f"   📝 Total de Testes: {total}\n")
    
    # Tabela de resultados
    if test_results:
        table = Table(title="📋 Resultados Detalhados", show_header=True, header_style="bold cyan")
        table.add_column("Status", style="bold", width=12)
        table.add_column("Teste", width=50)
        table.add_column("Detalhes", style="dim", width=40)
        
        for r in test_results:
            table.add_row(r['status'], r['name'], r['message'][:40])
        
        console.print(table)
    
    console.print()
    
    # Veredicto Final
    if success_rate == 100:
        console.print(Panel(
            "[bold green]✅ SISTEMA 100% PRONTO PARA PRODUÇÃO!\n\n"
            "Todos os testes passaram com sucesso.\n"
            "O sistema pode ser deployado no Railway com segurança.\n\n"
            "Próximos passos:\n"
            "1. Commit das mudanças\n"
            "2. Push para o repositório\n"
            "3. Deploy no Railway\n"
            "4. Monitorar logs após deploy[/bold green]",
            border_style="green",
            title="🚀 PRONTO PARA DEPLOY"
        ))
        return True
    elif success_rate >= 90:
        console.print(Panel(
            f"[bold yellow]⚠️  SISTEMA QUASE PRONTO ({success_rate:.1f}%)\n\n"
            f"{failed} teste(s) falharam.\n"
            f"Revise os problemas acima antes do deploy.\n\n"
            f"Recomendação: Corrija os erros e execute novamente.[/bold yellow]",
            border_style="yellow",
            title="⚠️  QUASE PRONTO"
        ))
        return False
    else:
        console.print(Panel(
            f"[bold red]❌ SISTEMA NÃO ESTÁ PRONTO ({success_rate:.1f}%)\n\n"
            f"{failed} teste(s) críticos falharam.\n"
            f"NÃO faça deploy até corrigir todos os problemas.\n\n"
            f"Revise os erros detalhados acima.[/bold red]",
            border_style="red",
            title="❌ NÃO DEPLOYAR"
        ))
        return False

async def main():
    """Executa todos os testes de prontidão."""
    console.print("\n[bold magenta]╔" + "="*78 + "╗[/bold magenta]")
    console.print("[bold magenta]║" + " "*20 + "TESTE DE PRONTIDÃO PARA PRODUÇÃO" + " "*26 + "║[/bold magenta]")
    console.print("[bold magenta]║" + " "*24 + "Sistema Multi-Agente - Railway Deploy" + " "*17 + "║[/bold magenta]")
    console.print("[bold magenta]╚" + "="*78 + "╝[/bold magenta]")
    
    console.print(f"\n[cyan]📅 Data:[/cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"[cyan]🤖 Provider:[/cyan] {llm_config['provider']}")
    console.print(f"[cyan]🧠 Model:[/cyan] {llm_config['model']}")
    console.print(f"[cyan]🔧 Python:[/cyan] {sys.version.split()[0]}\n")
    
    # Executar testes
    results = []
    results.append(check_env_vars())
    results.append(check_dependencies())
    results.append(check_agent_files())
    results.append(await check_agent_initialization())
    results.append(await check_supervisor_classification())
    results.append(await check_escalation_preparation())
    results.append(check_requirements())
    
    # Gerar relatório
    ready = generate_report()
    
    # Exit code
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Teste interrompido pelo usuário[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Erro fatal: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
