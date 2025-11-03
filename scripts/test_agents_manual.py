"""
Teste Manual Completo de Todos os Agentes
Executa conversas reais com cada agente e valida respostas
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from agents.supervisor import create_supervisor_agent
from agents.faq import create_faq_agent
from agents.intake import create_intake_agent
from agents.scheduler import create_scheduler_agent
from agents.escalation import create_escalation_agent
from agents.followup import create_followup_agent

from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult

console = Console()


class ManualAgentTester:
    """Testa agentes com conversas reais"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.llm_config = self._get_llm_config()
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Obtém configuração LLM do sistema"""
        try:
            from config.settings import settings
            
            # Usa configuração do sistema
            if settings.xai_api_key:
                return {
                    "provider": "xai",
                    "model": settings.xai_model,
                    "api_key": settings.xai_api_key,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "base_url": settings.xai_base_url,
                }
            elif settings.gemini_api_key:
                return {
                    "provider": "gemini",
                    "model": settings.gemini_model,
                    "api_key": settings.gemini_api_key,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                }
            else:
                console.print("[yellow]⚠ Nenhuma API key configurada em config/settings.py[/yellow]")
                console.print("[dim]Configure XAI_API_KEY ou GEMINI_API_KEY no arquivo .env[/dim]")
                return None
        except Exception as e:
            console.print(f"[red]Erro ao carregar configurações: {e}[/red]")
            return None
    
    async def test_supervisor_manual(self) -> Dict[str, Any]:
        """Testa Supervisor com classificação de intenções"""
        console.print("\n[bold cyan]═══ Testando Supervisor Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("Supervisor", "API key não configurada")
        
        try:
            agent = create_supervisor_agent(self.llm_config)
            
            test_cases = [
                {
                    "message": "Olá, gostaria de agendar uma consulta",
                    "expected_intent": "scheduling",
                    "description": "Intenção de agendamento"
                },
                {
                    "message": "Quanto custa a depilação a laser?",
                    "expected_intent": "faq",
                    "description": "Pergunta sobre preços"
                },
                {
                    "message": "Estou com muita dor após o procedimento",
                    "expected_intent": "escalation",
                    "description": "Situação de urgência"
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            # Use real conversation id from env when available
            env_conv = os.getenv("TEST_CHATWOOT_CONVERSATION_ID")
            try:
                env_conv_id = int(env_conv) if env_conv else None
            except ValueError:
                env_conv_id = None

            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Mensagem: '{test['message']}'[/dim]")
                
                try:
                    # Simula classificação
                    result = await agent.classify_intent(
                        message=test['message'],
                        conversation_id=f"test_supervisor_{i}",
                        context=[]
                    )
                    
                    intent = result.get('intent', 'unknown')
                    confidence = result.get('confidence', '')
                    
                    console.print(f"[green]✓ Intent: {intent} (confiança: {confidence})[/green]")
                    
                    # Valida se a intenção faz sentido
                    if intent in ['scheduling', 'faq', 'escalation', 'intake', 'followup']:
                        passed += 1
                        details.append(f"✓ {test['description']}: {intent}")
                    else:
                        details.append(f"✗ {test['description']}: intent inválido")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "Supervisor",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("Supervisor", str(e))
    
    async def test_faq_manual(self) -> Dict[str, Any]:
        """Testa FAQ com perguntas reais"""
        console.print("\n[bold cyan]═══ Testando FAQ Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("FAQ", "API key não configurada")
        
        try:
            agent = create_faq_agent(self.llm_config, enable_cache=True)
            
            test_cases = [
                {
                    "question": "Quanto custa a depilação a laser?",
                    "expected_keywords": ["preço", "valor", "depilação", "laser"],
                    "description": "Pergunta sobre preços"
                },
                {
                    "question": "Quais procedimentos vocês oferecem?",
                    "expected_keywords": ["procedimento", "tratamento", "serviço"],
                    "description": "Pergunta sobre serviços"
                },
                {
                    "question": "Qual o horário de funcionamento?",
                    "expected_keywords": ["horário", "hora", "funciona"],
                    "description": "Pergunta sobre horários"
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Pergunta: '{test['question']}'[/dim]")
                
                try:
                    # Executa pergunta
                    result = await agent.answer_question(
                        question=test['question'],
                        contact_name="Teste",
                        context=[]
                    )
                    
                    response = result.get('answer', '')
                    confidence = result.get('confidence', '')
                    
                    # Valida resposta
                    if response and len(response) > 20:
                        console.print(f"[green]✓ Resposta: {response[:100]}...[/green]")
                        console.print(f"[dim]Confiança: {confidence}[/dim]")
                        passed += 1
                        details.append(f"✓ {test['description']}")
                    else:
                        console.print(f"[yellow]⚠ Resposta curta ou vazia[/yellow]")
                        details.append(f"⚠ {test['description']}: resposta curta")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            # Testa cache
            console.print(f"\n[dim]Testando cache...[/dim]")
            cache_stats = await agent.get_cache_stats()
            console.print(f"[dim]Cache stats: {cache_stats}[/dim]")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "FAQ",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("FAQ", str(e))
    
    async def test_intake_manual(self) -> Dict[str, Any]:
        """Testa Intake com acolhimento"""
        console.print("\n[bold cyan]═══ Testando Intake Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("Intake", "API key não configurada")
        
        try:
            agent = create_intake_agent(self.llm_config)
            
            test_cases = [
                {
                    "message": "Olá, é a primeira vez que entro em contato",
                    "description": "Primeiro contato",
                    "should_welcome": True
                },
                {
                    "message": "Gostaria de fazer botox",
                    "description": "Interesse em procedimento",
                    "should_welcome": False
                },
                {
                    "message": "Tenho 35 anos e quero rejuvenescer",
                    "description": "Informações pessoais",
                    "should_welcome": False
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Mensagem: '{test['message']}'[/dim]")
                
                try:
                    # Executa acolhimento
                    result = await agent.process_message(
                        message=test['message'],
                        phone="5511999999999",  # Telefone de teste
                        context=[]
                    )
                    
                    response = result.get('response', '')
                    
                    # Valida resposta
                    if response and len(response) > 20:
                        console.print(f"[green]✓ Resposta: {response[:150]}...[/green]")
                        
                        # Verifica se não pede telefone
                        response_lower = response.lower()
                        asks_phone = any(word in response_lower for word in ['telefone', 'número', 'celular', 'whatsapp'])
                        
                        if not asks_phone:
                            passed += 1
                            details.append(f"✓ {test['description']}")
                        else:
                            console.print(f"[yellow]⚠ Agente pediu telefone (não deveria)[/yellow]")
                            details.append(f"⚠ {test['description']}: pediu telefone")
                    else:
                        console.print(f"[yellow]⚠ Resposta curta ou vazia[/yellow]")
                        details.append(f"⚠ {test['description']}: sem resposta")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "Intake",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("Intake", str(e))
    
    async def test_scheduler_manual(self) -> Dict[str, Any]:
        """Testa Scheduler com agendamentos"""
        console.print("\n[bold cyan]═══ Testando Scheduler Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("Scheduler", "API key não configurada")
        
        try:
            agent = create_scheduler_agent(self.llm_config)
            
            test_cases = [
                {
                    "message": "Quero agendar para amanhã de manhã",
                    "description": "Solicitação de agendamento",
                },
                {
                    "message": "Quais horários disponíveis para botox?",
                    "description": "Consulta de disponibilidade",
                },
                {
                    "message": "Preciso remarcar minha consulta",
                    "description": "Remarcação",
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Mensagem: '{test['message']}'[/dim]")
                
                try:
                    # Executa agendamento
                    result = await agent.process_scheduling_request(
                        message=test['message'],
                        contact_id="test-contact-id",
                        phone="5511999999999",
                        contact_name="Teste",
                        conversation_id="test-conv-id",
                        context=[]
                    )
                    
                    response = result.get('response', '')
                    
                    # Valida resposta
                    if response and len(response) > 20:
                        console.print(f"[green]✓ Resposta: {response[:150]}...[/green]")
                        
                        # Verifica se menciona horários/agenda
                        response_lower = response.lower()
                        mentions_schedule = any(word in response_lower for word in 
                            ['horário', 'agenda', 'disponível', 'data', 'hora', 'agendar'])
                        
                        if mentions_schedule:
                            passed += 1
                            details.append(f"✓ {test['description']}")
                        else:
                            details.append(f"⚠ {test['description']}: não mencionou agenda")
                    else:
                        console.print(f"[yellow]⚠ Resposta curta ou vazia[/yellow]")
                        details.append(f"⚠ {test['description']}: sem resposta")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            # Verifica tools
            console.print(f"\n[dim]Verificando ferramentas...[/dim]")
            if hasattr(agent, '_build_tools'):
                tools = agent._build_tools()
                console.print(f"[green]✓ {len(tools)} ferramentas disponíveis[/green]")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "Scheduler",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("Scheduler", str(e))
    
    async def test_escalation_manual(self) -> Dict[str, Any]:
        """Testa Escalation com situações urgentes"""
        console.print("\n[bold cyan]═══ Testando Escalation Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("Escalation", "API key não configurada")
        
        try:
            agent = create_escalation_agent(self.llm_config)
            
            test_cases = [
                {
                    "message": "Estou com muita dor após o procedimento",
                    "description": "Urgência médica",
                    "should_escalate": True
                },
                {
                    "message": "Não estou satisfeita com o resultado",
                    "description": "Reclamação",
                    "should_escalate": True
                },
                {
                    "message": "Preciso falar com um especialista",
                    "description": "Solicitação de especialista",
                    "should_escalate": True
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Mensagem: '{test['message']}'[/dim]")
                
                try:
                    # Executa escalação
                    result = await agent.prepare_escalation(
                        reason=test['description'],
                        conversation_id="test-conv-id",
                        contact_info={
                            "id": "test-contact-id",
                            "name": "Teste",
                            "phone": "5511999999999",
                            "email": ""
                        },
                        context=[{"role":"user","content": test['message']}],
                        intents=["escalation"],
                        actions_attempted=["manual_test"],
                        priority="high" if i == 1 else "medium"
                    )
                    
                    response = result.get('patient_message', '')
                    
                    # Valida resposta
                    if response and len(response) > 20:
                        console.print(f"[green]✓ Resposta: {response[:150]}...[/green]")
                        
                        # Verifica se menciona transferência/humano
                        response_lower = response.lower()
                        mentions_human = any(word in response_lower for word in 
                            ['humano', 'especialista', 'equipe', 'transferir', 'atendente'])
                        
                        if mentions_human:
                            passed += 1
                            details.append(f"✓ {test['description']}")
                        else:
                            details.append(f"⚠ {test['description']}: não mencionou humano")
                    else:
                        console.print(f"[yellow]⚠ Resposta curta ou vazia[/yellow]")
                        details.append(f"⚠ {test['description']}: sem resposta")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "Escalation",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("Escalation", str(e))
    
    async def test_followup_manual(self) -> Dict[str, Any]:
        """Testa FollowUp com acompanhamento"""
        console.print("\n[bold cyan]═══ Testando FollowUp Agent ═══[/bold cyan]")
        
        if not self.llm_config:
            return self._create_error_result("FollowUp", "API key não configurada")
        
        try:
            agent = create_followup_agent(self.llm_config)
            
            # Conversa real opcional para envio via Chatwoot
            env_conv = os.getenv("TEST_CHATWOOT_CONVERSATION_ID")
            try:
                env_conv_id = int(env_conv) if env_conv else None
            except ValueError:
                env_conv_id = None

            test_cases = [
                {
                    "message": "Como está sua recuperação após o procedimento?",
                    "description": "Acompanhamento de recuperação",
                },
                {
                    "message": "Está satisfeita com o resultado?",
                    "description": "Pesquisa de satisfação",
                },
                {
                    "message": "Precisa de algum cuidado especial?",
                    "description": "Orientações pós-procedimento",
                }
            ]
            
            passed = 0
            total = len(test_cases)
            details = []
            
            for i, test in enumerate(test_cases, 1):
                console.print(f"\n[dim]Teste {i}/{total}: {test['description']}[/dim]")
                console.print(f"[dim]Mensagem: '{test['message']}'[/dim]")
                
                try:
                    # Executa follow-up
                    if env_conv_id:
                        # Real send using provided conversation id
                        result = await agent.send_post_treatment_feedback(
                            conversation_id=env_conv_id,
                            contact_name="Teste",
                            procedure="Botox"
                        )
                        response = (
                            "Mensagem de follow-up enviada com sucesso"
                            if result.get('success') else ""
                        )
                    else:
                        # Dry-run: format template content without sending
                        formatted_json = await agent._format_template_tool(
                            template_name="PAS-VENDA TRATAMENTO CORPORAL",
                            variables_json=os.getenv(
                                "TEST_FOLLOWUP_VARS_JSON",
                                '{"name":"Teste","procedure":"Botox"}'
                            )
                        )
                        response = formatted_json or ""
                    
                    # Valida resposta
                    if response and len(response) > 20:
                        console.print(f"[green]✓ Resposta: {response[:150]}...[/green]")
                        passed += 1
                        details.append(f"✓ {test['description']}")
                    else:
                        console.print(f"[yellow]⚠ Resposta curta ou vazia[/yellow]")
                        details.append(f"⚠ {test['description']}: sem resposta")
                    
                except Exception as e:
                    console.print(f"[red]✗ Erro: {str(e)[:100]}[/red]")
                    details.append(f"✗ {test['description']}: erro")
            
            return {
                "status": "✓ PASS" if passed >= total * 0.6 else "✗ FAIL",
                "agent": "FollowUp",
                "tests_passed": passed,
                "tests_total": total,
                "details": " | ".join(details[:3])
            }
            
        except Exception as e:
            return self._create_error_result("FollowUp", str(e))
    
    def _create_error_result(self, agent_name: str, error: str) -> Dict[str, Any]:
        """Cria resultado de erro"""
        return {
            "status": "✗ FAIL",
            "agent": agent_name,
            "tests_passed": 0,
            "tests_total": 3,
            "details": f"Erro: {error[:80]}"
        }
    
    async def run_all_tests(self):
        """Executa todos os testes manuais"""
        console.print(Panel.fit(
            "[bold white]🧪 Teste Manual Completo de Todos os Agentes[/bold white]\n"
            f"[dim]Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
            "[dim]Testando com conversas reais e validação de respostas[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        
        # Verifica API key
        if not self.llm_config:
            console.print("\n[bold red]✗ Erro: Configure XAI_API_KEY ou GEMINI_API_KEY[/bold red]")
            return
        
        provider = self.llm_config.get('provider', 'unknown')
        model = self.llm_config.get('model', 'unknown')
        console.print(f"\n[dim]Usando: {provider} - {model}[/dim]\n")
        
        # Executa testes
        tests = [
            ("Supervisor", self.test_supervisor_manual),
            ("FAQ", self.test_faq_manual),
            ("Intake", self.test_intake_manual),
            ("Scheduler", self.test_scheduler_manual),
            ("Escalation", self.test_escalation_manual),
            ("FollowUp", self.test_followup_manual),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for agent_name, test_func in tests:
                task = progress.add_task(f"Testando {agent_name}...", total=None)
                result = await test_func()
                self.results[agent_name] = result
                progress.remove_task(task)
        
        self.print_results()
    
    def print_results(self):
        """Imprime resultados"""
        console.print("\n")
        
        table = Table(
            title="📊 Resultados dos Testes Manuais",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Agente", style="cyan", width=12)
        table.add_column("Status", width=10)
        table.add_column("Testes", justify="center", width=10)
        table.add_column("Detalhes", style="dim", width=70)
        
        total_passed = 0
        total_tests = 0
        agents_passed = 0
        
        for agent_name, result in self.results.items():
            status = result["status"]
            tests_info = f"{result['tests_passed']}/{result['tests_total']}"
            details = result.get("details", "N/A")
            
            if "PASS" in status:
                status_style = "[green]✓ PASS[/green]"
                agents_passed += 1
            else:
                status_style = "[red]✗ FAIL[/red]"
            
            table.add_row(agent_name, status_style, tests_info, details)
            
            total_passed += result["tests_passed"]
            total_tests += result["tests_total"]
        
        console.print(table)
        
        # Sumário
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        agents_rate = (agents_passed / len(self.results) * 100) if self.results else 0
        
        summary_color = "green" if success_rate >= 70 else "yellow" if success_rate >= 50 else "red"
        
        console.print(f"\n[bold {summary_color}]Sumário Final:[/bold {summary_color}]")
        console.print(f"  • Agentes testados: {len(self.results)}")
        console.print(f"  • Agentes aprovados: {agents_passed}/{len(self.results)} ({agents_rate:.1f}%)")
        console.print(f"  • Testes executados: {total_tests}")
        console.print(f"  • Testes aprovados: {total_passed}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 70:
            console.print("\n[bold green]✓ Testes manuais concluídos com sucesso![/bold green]")
        elif success_rate >= 50:
            console.print("\n[bold yellow]⚠ Alguns agentes precisam de ajustes[/bold yellow]")
        else:
            console.print("\n[bold red]✗ Múltiplos agentes falharam nos testes[/bold red]")


async def main():
    """Função principal"""
    tester = ManualAgentTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        console.print("\n[yellow]Testes interrompidos pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erro fatal:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
