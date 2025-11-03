"""
Script de teste completo para todos os agentes do sistema.
Valida inicialização, configuração e funcionalidade básica de cada agente.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


class AgentTester:
    """Testa todos os agentes do sistema"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.llm_config = self._get_test_llm_config()
    
    def _get_test_llm_config(self) -> Dict[str, Any]:
        """Obtém configuração LLM para testes"""
        # Tenta usar xAI se disponível, senão usa configuração mínima
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "test-key"
        
        return {
            "provider": "xai",
            "model": "grok-beta",
            "api_key": api_key,
            "temperature": 0.7,
            "max_tokens": 2048,
            "base_url": "https://api.x.ai/v1",
        }
        
    async def test_supervisor(self) -> Dict[str, Any]:
        """Testa o agente Supervisor"""
        console.print("\n[bold cyan]Testando Supervisor Agent...[/bold cyan]")
        
        try:
            from agents.supervisor import create_supervisor_agent
            
            # Teste 1: Inicialização
            agent = create_supervisor_agent(self.llm_config)
            
            # Teste 2: Verificar atributos essenciais
            assert hasattr(agent, 'agent'), "Supervisor deve ter atributo 'agent'"
            assert hasattr(agent, 'model_client'), "Supervisor deve ter 'model_client'"
            
            # Teste 3: Verificar routing history
            assert hasattr(agent, 'routing_history'), "Supervisor deve ter 'routing_history'"
            
            return {
                "status": "✓ PASS",
                "agent": "Supervisor",
                "tests_passed": 3,
                "tests_total": 3,
                "details": "Inicialização OK, atributos OK, routing history OK"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "Supervisor",
                "tests_passed": 0,
                "tests_total": 3,
                "error": str(e)
            }
    
    async def test_faq(self) -> Dict[str, Any]:
        """Testa o agente FAQ"""
        console.print("\n[bold cyan]Testando FAQ Agent...[/bold cyan]")
        
        try:
            from agents.faq import create_faq_agent
            
            # Teste 1: Inicialização
            agent = create_faq_agent(self.llm_config, enable_cache=True)
            
            # Teste 2: Verificar model client
            assert hasattr(agent, 'model_client'), "FAQ deve ter 'model_client'"
            
            # Teste 3: Verificar agent
            assert hasattr(agent, 'agent'), "FAQ deve ter 'agent'"
            
            # Teste 4: Verificar cache (se habilitado)
            assert hasattr(agent, '_cache'), "FAQ deve ter '_cache'"
            
            return {
                "status": "✓ PASS",
                "agent": "FAQ",
                "tests_passed": 4,
                "tests_total": 4,
                "details": "Inicialização OK, model client OK, agent OK, cache OK"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "FAQ",
                "tests_passed": 0,
                "tests_total": 4,
                "error": str(e)
            }
    
    async def test_intake(self) -> Dict[str, Any]:
        """Testa o agente Intake"""
        console.print("\n[bold cyan]Testando Intake Agent...[/bold cyan]")
        
        try:
            from agents.intake import create_intake_agent, INTAKE_SYSTEM_PROMPT
            
            # Teste 1: Inicialização
            agent = create_intake_agent(self.llm_config)
            
            # Teste 2: Verificar model client e agent
            assert hasattr(agent, 'model_client'), "Intake deve ter 'model_client'"
            assert hasattr(agent, 'agent'), "Intake deve ter 'agent'"
            
            # Teste 3: Verificar prompt system
            system_msg = INTAKE_SYSTEM_PROMPT.lower()
            required_concepts = ['acolh', 'necessidade', 'paciente']
            
            concepts_found = sum(1 for concept in required_concepts if concept in system_msg)
            assert concepts_found >= 2, f"Intake deve ter conceitos de acolhimento (encontrados: {concepts_found}/3)"
            
            # Teste 4: Verificar que não solicita telefone (usa WhatsApp implicitamente)
            assert 'whatsapp' in system_msg or 'não solicitar' in system_msg, \
                "Intake deve usar WhatsApp implicitamente"
            
            return {
                "status": "✓ PASS",
                "agent": "Intake",
                "tests_passed": 4,
                "tests_total": 4,
                "details": f"Inicialização OK, atributos OK, conceitos OK ({concepts_found}/3), WhatsApp OK"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "Intake",
                "tests_passed": 0,
                "tests_total": 4,
                "error": str(e)
            }
    
    async def test_scheduler(self) -> Dict[str, Any]:
        """Testa o agente Scheduler"""
        console.print("\n[bold cyan]Testando Scheduler Agent...[/bold cyan]")
        
        try:
            from agents.scheduler import create_scheduler_agent
            
            # Teste 1: Inicialização
            agent = create_scheduler_agent(self.llm_config)
            
            # Teste 2: Verificar atributos essenciais
            assert hasattr(agent, 'model_client'), "Scheduler deve ter 'model_client'"
            assert hasattr(agent, 'agent'), "Scheduler deve ter 'agent'"
            
            # Teste 3: Verificar método _build_tools
            assert hasattr(agent, '_build_tools'), "Scheduler deve ter método '_build_tools'"
            
            # Teste 4: Verificar que o agent interno tem tools
            assert hasattr(agent.agent, '_tools') or hasattr(agent.agent, 'tools'), \
                "Scheduler.agent deve ter ferramentas configuradas"
            
            return {
                "status": "✓ PASS",
                "agent": "Scheduler",
                "tests_passed": 4,
                "tests_total": 4,
                "details": "Inicialização OK, atributos OK, _build_tools OK, agent.tools OK"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "Scheduler",
                "tests_passed": 0,
                "tests_total": 4,
                "error": str(e)
            }
    
    async def test_escalation(self) -> Dict[str, Any]:
        """Testa o agente Escalation"""
        console.print("\n[bold cyan]Testando Escalation Agent...[/bold cyan]")
        
        try:
            from agents.escalation import create_escalation_agent, ESCALATION_SYSTEM_PROMPT
            
            # Teste 1: Inicialização
            agent = create_escalation_agent(self.llm_config)
            
            # Teste 2: Verificar atributos
            assert hasattr(agent, 'model_client'), "Escalation deve ter 'model_client'"
            assert hasattr(agent, 'agent'), "Escalation deve ter 'agent'"
            
            # Teste 3: Verificar critérios de escalação no prompt
            system_msg = ESCALATION_SYSTEM_PROMPT.lower()
            escalation_concepts = ['urgente', 'emergência', 'complicação', 'humano', 'especialista', 'crítico']
            
            concepts_found = sum(1 for concept in escalation_concepts if concept in system_msg)
            assert concepts_found >= 2, f"Escalation deve ter critérios claros (encontrados: {concepts_found}/6)"
            
            return {
                "status": "✓ PASS",
                "agent": "Escalation",
                "tests_passed": 3,
                "tests_total": 3,
                "details": f"Inicialização OK, atributos OK, critérios OK ({concepts_found}/6)"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "Escalation",
                "tests_passed": 0,
                "tests_total": 3,
                "error": str(e)
            }
    
    async def test_followup(self) -> Dict[str, Any]:
        """Testa o agente FollowUp"""
        console.print("\n[bold cyan]Testando FollowUp Agent...[/bold cyan]")
        
        try:
            from agents.followup import create_followup_agent, FOLLOWUP_SYSTEM_PROMPT
            
            # Teste 1: Inicialização
            agent = create_followup_agent(self.llm_config)
            
            # Teste 2: Verificar atributos
            assert hasattr(agent, 'model_client'), "FollowUp deve ter 'model_client'"
            assert hasattr(agent, 'agent'), "FollowUp deve ter 'agent'"
            
            # Teste 3: Verificar foco em pós-atendimento
            system_msg = FOLLOWUP_SYSTEM_PROMPT.lower()
            followup_concepts = ['acompanhamento', 'follow', 'pós', 'recuperação', 'satisfação', 'retorno']
            
            concepts_found = sum(1 for concept in followup_concepts if concept in system_msg)
            assert concepts_found >= 2, f"FollowUp deve focar em pós-atendimento (encontrados: {concepts_found}/6)"
            
            return {
                "status": "✓ PASS",
                "agent": "FollowUp",
                "tests_passed": 3,
                "tests_total": 3,
                "details": f"Inicialização OK, atributos OK, foco pós-atendimento OK ({concepts_found}/6)"
            }
            
        except Exception as e:
            return {
                "status": "✗ FAIL",
                "agent": "FollowUp",
                "tests_passed": 0,
                "tests_total": 3,
                "error": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes"""
        console.print(Panel.fit(
            "[bold white]Teste Completo de Todos os Agentes[/bold white]\n"
            f"[dim]Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        
        # Lista de testes a executar
        tests = [
            ("Supervisor", self.test_supervisor),
            ("FAQ", self.test_faq),
            ("Intake", self.test_intake),
            ("Scheduler", self.test_scheduler),
            ("Escalation", self.test_escalation),
            ("FollowUp", self.test_followup),
        ]
        
        # Executa cada teste
        for agent_name, test_func in tests:
            result = await test_func()
            self.results[agent_name] = result
        
        return self.results
    
    def print_results(self):
        """Imprime os resultados em formato de tabela"""
        console.print("\n")
        
        # Cria tabela de resultados
        table = Table(
            title="📊 Resultados dos Testes de Agentes",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Agente", style="cyan", width=15)
        table.add_column("Status", width=10)
        table.add_column("Testes", justify="center", width=12)
        table.add_column("Detalhes", style="dim", width=60)
        
        total_passed = 0
        total_tests = 0
        agents_passed = 0
        
        for agent_name, result in self.results.items():
            status = result["status"]
            tests_info = f"{result['tests_passed']}/{result['tests_total']}"
            details = result.get("details", result.get("error", "N/A"))
            
            # Define cor baseada no status
            if "PASS" in status:
                status_style = "[green]✓ PASS[/green]"
                agents_passed += 1
            else:
                status_style = "[red]✗ FAIL[/red]"
            
            table.add_row(
                agent_name,
                status_style,
                tests_info,
                details[:60]
            )
            
            total_passed += result["tests_passed"]
            total_tests += result["tests_total"]
        
        console.print(table)
        
        # Sumário final
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        agents_rate = (agents_passed / len(self.results) * 100) if self.results else 0
        
        summary_color = "green" if success_rate >= 80 else "yellow" if success_rate >= 60 else "red"
        
        console.print(f"\n[bold {summary_color}]Sumário Final:[/bold {summary_color}]")
        console.print(f"  • Agentes testados: {len(self.results)}")
        console.print(f"  • Agentes aprovados: {agents_passed}/{len(self.results)} ({agents_rate:.1f}%)")
        console.print(f"  • Testes executados: {total_tests}")
        console.print(f"  • Testes aprovados: {total_passed}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            console.print("\n[bold green]✓ Sistema de agentes está funcionando corretamente![/bold green]")
        elif success_rate >= 60:
            console.print("\n[bold yellow]⚠ Sistema de agentes precisa de atenção[/bold yellow]")
        else:
            console.print("\n[bold red]✗ Sistema de agentes requer correções urgentes[/bold red]")
        
        return success_rate >= 80


async def main():
    """Função principal"""
    tester = AgentTester()
    
    try:
        await tester.run_all_tests()
        success = tester.print_results()
        
        # Retorna código de saída apropriado
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Testes interrompidos pelo usuário[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Erro fatal durante os testes:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
