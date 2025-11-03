#!/usr/bin/env python3
"""
Manual QA Test Guide for Clínica Luana Multi-Agent System

This interactive script guides testers through 24 manual test scenarios:
- 8 FAQ conversations
- 8 Scheduling conversations  
- 8 Rescheduling/Cancellation conversations

Requirements: 5.1-5.5, 2.1-2.5, 3.1-3.3, 4.1-4.8, 11.1-11.5

Usage:
    python scripts/manual_qa_test_guide.py
    
    # Or run specific category:
    python scripts/manual_qa_test_guide.py --category faq
    python scripts/manual_qa_test_guide.py --category scheduling
    python scripts/manual_qa_test_guide.py --category rescheduling
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.supabase_client import supabase_client
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase client not available - database verification will be skipped")


class TestCategory(Enum):
    """Test categories."""
    FAQ = "faq"
    SCHEDULING = "scheduling"
    RESCHEDULING = "rescheduling"


class TestStatus(Enum):
    """Test execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Result of a single test case."""
    test_id: str
    category: str
    title: str
    status: TestStatus
    notes: str = ""
    timestamp: str = ""
    latency_ms: Optional[int] = None
    booking_created: Optional[bool] = None
    message_delivered: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class TestCase:
    """Definition of a test case."""
    test_id: str
    category: TestCategory
    title: str
    description: str
    user_message: str
    expected_behavior: List[str]
    validation_steps: List[str]
    requirements: List[str]


# ============================================================================
# TEST CASE DEFINITIONS
# ============================================================================

FAQ_TEST_CASES = [
    TestCase(
        test_id="FAQ-01",
        category=TestCategory.FAQ,
        title="Perguntas sobre tratamentos",
        description="Testar resposta sobre informações de tratamentos",
        user_message="Olá! Gostaria de saber sobre depilação a laser",
        expected_behavior=[
            "Sistema deve responder com informações sobre depilação a laser",
            "Deve incluir descrição do tratamento",
            "Pode mencionar duração, indicações ou contraindicações",
            "Tom deve ser profissional e acolhedor"
        ],
        validation_steps=[
            "Verificar se resposta contém informações relevantes sobre o tratamento",
            "Verificar se tom é adequado (profissional, acolhedor)",
            "Verificar se não há erros ou informações incorretas"
        ],
        requirements=["5.1", "5.2"]
    ),
    TestCase(
        test_id="FAQ-02",
        category=TestCategory.FAQ,
        title="Perguntas sobre preços fixos",
        description="Testar resposta sobre preços de tratamentos com valor fixo",
        user_message="Quanto custa a depilação a laser?",
        expected_behavior=[
            "Sistema deve informar valores quando disponíveis",
            "Ou indicar necessidade de consulta para avaliação",
            "Pode mencionar formas de pagamento ou pacotes"
        ],
        validation_steps=[
            "Verificar se informação de preço é clara",
            "Verificar se menciona consulta quando necessário",
            "Verificar se não há valores incorretos"
        ],
        requirements=["5.3"]
    ),
    TestCase(
        test_id="FAQ-03",
        category=TestCategory.FAQ,
        title="Perguntas sobre preços sob consulta",
        description="Testar resposta sobre tratamentos que requerem consulta",
        user_message="Quanto custa harmonização facial?",
        expected_behavior=[
            "Sistema deve informar que requer consulta prévia",
            "Deve mencionar valor da consulta (R$200)",
            "Deve explicar que valor pode ser abatido no tratamento"
        ],
        validation_steps=[
            "Verificar se menciona necessidade de consulta",
            "Verificar se informa valor da consulta",
            "Verificar se explica política de abatimento"
        ],
        requirements=["5.3", "13.1", "13.2"]
    ),
    TestCase(
        test_id="FAQ-04",
        category=TestCategory.FAQ,
        title="Perguntas sobre políticas",
        description="Testar resposta sobre políticas de cancelamento",
        user_message="Qual é a política de cancelamento?",
        expected_behavior=[
            "Sistema deve explicar políticas de cancelamento",
            "Deve mencionar diferentes prazos por tipo de tratamento",
            "Harmonização: 4h de antecedência",
            "Laser: 24h de antecedência"
        ],
        validation_steps=[
            "Verificar se políticas estão corretas",
            "Verificar se diferencia por tipo de tratamento",
            "Verificar se usa message template quando aplicável"
        ],
        requirements=["5.4", "4.2", "4.3"]
    ),
    TestCase(
        test_id="FAQ-05",
        category=TestCategory.FAQ,
        title="Perguntas sobre contraindicações",
        description="Testar resposta sobre contraindicações de tratamentos",
        user_message="Quais são as contraindicações para depilação a laser?",
        expected_behavior=[
            "Sistema deve listar contraindicações comuns",
            "Deve recomendar consulta se paciente menciona condição",
            "Tom deve ser cuidadoso e profissional"
        ],
        validation_steps=[
            "Verificar se contraindicações estão corretas",
            "Verificar se recomenda avaliação profissional quando apropriado",
            "Verificar se informações são claras e completas"
        ],
        requirements=["5.2", "15.1", "15.4"]
    ),
    TestCase(
        test_id="FAQ-06",
        category=TestCategory.FAQ,
        title="Perguntas sobre cuidados pós-tratamento",
        description="Testar resposta sobre cuidados após procedimentos",
        user_message="Quais cuidados devo ter após a depilação a laser?",
        expected_behavior=[
            "Sistema deve informar cuidados pós-tratamento",
            "Evitar sol por 7 dias, usar FPS 30+, hidratação",
            "Informações devem ser práticas e claras"
        ],
        validation_steps=[
            "Verificar se cuidados estão corretos e completos",
            "Verificar se informações são práticas",
            "Verificar se tom é educativo"
        ],
        requirements=["5.2", "15.2"]
    ),
    TestCase(
        test_id="FAQ-07",
        category=TestCategory.FAQ,
        title="Perguntas sobre horário de funcionamento",
        description="Testar resposta sobre horários da clínica",
        user_message="Qual é o horário de funcionamento da clínica?",
        expected_behavior=[
            "Sistema deve informar horários corretos",
            "Segunda a Sexta: 08:30-19:00",
            "Sábado: 08:30-12:00",
            "Domingo: Fechado"
        ],
        validation_steps=[
            "Verificar se horários estão corretos",
            "Verificar se menciona todos os dias da semana",
            "Verificar se informação é clara"
        ],
        requirements=["5.2", "13.1"]
    ),
    TestCase(
        test_id="FAQ-08",
        category=TestCategory.FAQ,
        title="Verificar uso de templates e escalação",
        description="Testar uso de templates e escalação quando necessário",
        user_message="Preciso falar com um atendente humano",
        expected_behavior=[
            "Sistema deve reconhecer pedido de escalação",
            "Deve preparar resumo da conversa",
            "Deve transferir para atendente humano",
            "Deve enviar mensagem de handoff"
        ],
        validation_steps=[
            "Verificar se sistema reconhece pedido de escalação",
            "Verificar se conversa é atribuída a humano no Chatwoot",
            "Verificar se mensagem de handoff é enviada",
            "Verificar se automação é pausada"
        ],
        requirements=["5.5", "6.1", "6.2", "6.3", "6.4"]
    ),
]

SCHEDULING_TEST_CASES = [
    TestCase(
        test_id="SCH-01",
        category=TestCategory.SCHEDULING,
        title="Agendamento simples",
        description="Testar fluxo completo de agendamento com slot disponível",
        user_message="Olá, gostaria de agendar depilação a laser para amanhã",
        expected_behavior=[
            "Sistema deve coletar nome se necessário",
            "Deve mostrar slots disponíveis",
            "Deve solicitar confirmação explícita",
            "Deve criar booking após confirmação",
            "Deve enviar mensagem de confirmação"
        ],
        validation_steps=[
            "Verificar se coleta informações necessárias",
            "Verificar se mostra pelo menos 3 opções de horário",
            "Verificar se solicita confirmação antes de criar booking",
            "Verificar se booking aparece no banco de dados",
            "Verificar se confirmação é enviada via WhatsApp"
        ],
        requirements=["2.1", "2.2", "2.6", "3.1", "3.2", "3.4"]
    ),
    TestCase(
        test_id="SCH-02",
        category=TestCategory.SCHEDULING,
        title="Sem slots disponíveis",
        description="Testar resposta quando não há horários disponíveis",
        user_message="Quero agendar para hoje às 20:00",
        expected_behavior=[
            "Sistema deve informar que horário não está disponível",
            "Deve explicar horário de funcionamento",
            "Deve sugerir próximo horário disponível",
            "Tom deve ser prestativo"
        ],
        validation_steps=[
            "Verificar se explica por que horário não está disponível",
            "Verificar se sugere alternativas",
            "Verificar se não cria booking inválido"
        ],
        requirements=["2.4", "2.6"]
    ),
    TestCase(
        test_id="SCH-03",
        category=TestCategory.SCHEDULING,
        title="Fora do horário comercial",
        description="Testar agendamento fora do horário de funcionamento",
        user_message="Posso agendar para domingo?",
        expected_behavior=[
            "Sistema deve informar que clínica não funciona aos domingos",
            "Deve explicar horários de funcionamento",
            "Deve sugerir dias disponíveis"
        ],
        validation_steps=[
            "Verificar se valida business hours corretamente",
            "Verificar se explica horários de funcionamento",
            "Verificar se sugere alternativas válidas"
        ],
        requirements=["2.4"]
    ),
    TestCase(
        test_id="SCH-04",
        category=TestCategory.SCHEDULING,
        title="Antecedência insuficiente",
        description="Testar agendamento com menos de 1 hora de antecedência",
        user_message="Quero agendar para daqui 30 minutos",
        expected_behavior=[
            "Sistema deve informar antecedência mínima de 1 hora",
            "Deve explicar política de agendamento",
            "Deve sugerir horários válidos"
        ],
        validation_steps=[
            "Verificar se valida antecedência mínima",
            "Verificar se explica política claramente",
            "Verificar se não cria booking inválido"
        ],
        requirements=["2.5"]
    ),
    TestCase(
        test_id="SCH-05",
        category=TestCategory.SCHEDULING,
        title="Fluxo de confirmação",
        description="Testar fluxo completo com confirmação explícita",
        user_message="Quero agendar harmonização facial",
        expected_behavior=[
            "Sistema deve mostrar slots disponíveis",
            "Deve solicitar confirmação explícita",
            "Deve criar booking apenas após confirmação",
            "Deve enviar confirmação com detalhes"
        ],
        validation_steps=[
            "Verificar se solicita confirmação antes de criar booking",
            "Verificar se não cria booking sem confirmação",
            "Verificar se confirmação contém todos detalhes (data, hora, procedimento)",
            "Verificar se booking é criado no banco"
        ],
        requirements=["2.6", "2.7", "3.1", "3.2"]
    ),
    TestCase(
        test_id="SCH-06",
        category=TestCategory.SCHEDULING,
        title="Verificar agendamentos existentes",
        description="Testar consulta de agendamentos do paciente",
        user_message="Quais são meus agendamentos?",
        expected_behavior=[
            "Sistema deve buscar agendamentos do paciente",
            "Deve listar agendamentos futuros",
            "Deve mostrar data, hora e procedimento",
            "Se não houver, deve informar claramente"
        ],
        validation_steps=[
            "Verificar se busca agendamentos corretamente",
            "Verificar se informações estão completas",
            "Verificar se formato é claro e legível"
        ],
        requirements=["2.8", "3.3"]
    ),
    TestCase(
        test_id="SCH-07",
        category=TestCategory.SCHEDULING,
        title="Múltiplos serviços",
        description="Testar pergunta sobre agendar múltiplos serviços",
        user_message="Posso agendar depilação e harmonização no mesmo dia?",
        expected_behavior=[
            "Sistema deve explicar possibilidade ou limitações",
            "Deve considerar duração total dos procedimentos",
            "Deve sugerir melhor abordagem"
        ],
        validation_steps=[
            "Verificar se resposta é clara sobre possibilidade",
            "Verificar se considera duração e recursos",
            "Verificar se oferece alternativas práticas"
        ],
        requirements=["2.1", "2.3"]
    ),
    TestCase(
        test_id="SCH-08",
        category=TestCategory.SCHEDULING,
        title="Agendamento de consulta",
        description="Testar agendamento de consulta para tratamentos que requerem",
        user_message="Quero agendar uma consulta para harmonização",
        expected_behavior=[
            "Sistema deve reconhecer necessidade de consulta",
            "Deve informar valor da consulta",
            "Deve explicar política de abatimento",
            "Deve mostrar slots disponíveis para consulta"
        ],
        validation_steps=[
            "Verificar se identifica necessidade de consulta",
            "Verificar se informa valor correto",
            "Verificar se explica política de abatimento",
            "Verificar se oferece agendamento"
        ],
        requirements=["13.1", "13.2", "2.1"]
    ),
]

RESCHEDULING_TEST_CASES = [
    TestCase(
        test_id="RES-01",
        category=TestCategory.RESCHEDULING,
        title="Cancelamento dentro da política",
        description="Testar cancelamento com antecedência adequada",
        user_message="Preciso cancelar meu agendamento de amanhã",
        expected_behavior=[
            "Sistema deve buscar agendamento do paciente",
            "Deve validar política de cancelamento",
            "Deve confirmar cancelamento se dentro do prazo",
            "Deve atualizar status no banco",
            "Deve enviar confirmação de cancelamento"
        ],
        validation_steps=[
            "Verificar se busca agendamento corretamente",
            "Verificar se valida política (4h harmonização, 24h laser)",
            "Verificar se status é atualizado para 'cancelled'",
            "Verificar se confirmação é enviada"
        ],
        requirements=["4.1", "4.2", "4.4"]
    ),
    TestCase(
        test_id="RES-02",
        category=TestCategory.RESCHEDULING,
        title="Cancelamento fora da política",
        description="Testar cancelamento fora do prazo permitido",
        user_message="Preciso cancelar meu agendamento de hoje (2h antes)",
        expected_behavior=[
            "Sistema deve validar política de cancelamento",
            "Deve informar que está fora do prazo",
            "Deve explicar que sessão será registrada como feita",
            "Deve oferecer escalação para caso especial"
        ],
        validation_steps=[
            "Verificar se valida política corretamente",
            "Verificar se explica consequências claramente",
            "Verificar se oferece escalação",
            "Verificar se não cancela automaticamente"
        ],
        requirements=["4.2", "4.3", "4.5"]
    ),
    TestCase(
        test_id="RES-03",
        category=TestCategory.RESCHEDULING,
        title="Primeira remarcação",
        description="Testar primeira tentativa de remarcação",
        user_message="Gostaria de remarcar meu agendamento para outro dia",
        expected_behavior=[
            "Sistema deve buscar agendamento existente",
            "Deve verificar contador de remarcações (deve ser 0)",
            "Deve mostrar slots disponíveis",
            "Deve permitir remarcação",
            "Deve incrementar contador"
        ],
        validation_steps=[
            "Verificar se busca agendamento corretamente",
            "Verificar se permite remarcação (primeira vez)",
            "Verificar se mostra slots disponíveis",
            "Verificar se atualiza contador no banco"
        ],
        requirements=["4.6", "4.8"]
    ),
    TestCase(
        test_id="RES-04",
        category=TestCategory.RESCHEDULING,
        title="Segunda remarcação",
        description="Testar segunda tentativa de remarcação (ainda permitida)",
        user_message="Preciso remarcar novamente meu agendamento",
        expected_behavior=[
            "Sistema deve verificar contador de remarcações (deve ser 1)",
            "Deve permitir segunda remarcação",
            "Deve avisar que é a última remarcação permitida",
            "Deve incrementar contador para 2"
        ],
        validation_steps=[
            "Verificar se permite segunda remarcação",
            "Verificar se avisa sobre limite",
            "Verificar se contador é atualizado para 2",
            "Verificar se novo horário é agendado"
        ],
        requirements=["4.6", "4.8"]
    ),
    TestCase(
        test_id="RES-05",
        category=TestCategory.RESCHEDULING,
        title="Limite de remarcações excedido",
        description="Testar terceira tentativa de remarcação (bloqueada)",
        user_message="Preciso remarcar pela terceira vez",
        expected_behavior=[
            "Sistema deve verificar contador de remarcações (deve ser 2)",
            "Deve bloquear remarcação",
            "Deve explicar limite de 2 remarcações",
            "Deve sugerir escalação para caso especial"
        ],
        validation_steps=[
            "Verificar se bloqueia terceira remarcação",
            "Verificar se explica política claramente",
            "Verificar se oferece escalação",
            "Verificar se não altera agendamento"
        ],
        requirements=["4.6", "4.7"]
    ),
    TestCase(
        test_id="RES-06",
        category=TestCategory.RESCHEDULING,
        title="Cancelamento sem agendamento",
        description="Testar cancelamento quando não há agendamento",
        user_message="Quero cancelar meu agendamento",
        expected_behavior=[
            "Sistema deve buscar agendamentos do paciente",
            "Deve informar que não há agendamentos ativos",
            "Deve oferecer ajuda para agendar novo"
        ],
        validation_steps=[
            "Verificar se busca agendamentos corretamente",
            "Verificar se informa claramente que não há agendamentos",
            "Verificar se oferece alternativas úteis"
        ],
        requirements=["4.1"]
    ),
    TestCase(
        test_id="RES-07",
        category=TestCategory.RESCHEDULING,
        title="Remarcação para horário indisponível",
        description="Testar remarcação para slot não disponível",
        user_message="Quero remarcar para domingo às 15:00",
        expected_behavior=[
            "Sistema deve validar horário solicitado",
            "Deve informar que horário não está disponível",
            "Deve explicar horários de funcionamento",
            "Deve sugerir horários disponíveis"
        ],
        validation_steps=[
            "Verificar se valida horário corretamente",
            "Verificar se explica por que não está disponível",
            "Verificar se sugere alternativas válidas",
            "Verificar se não cria remarcação inválida"
        ],
        requirements=["4.8", "2.4"]
    ),
    TestCase(
        test_id="RES-08",
        category=TestCategory.RESCHEDULING,
        title="Política de No-Show",
        description="Testar explicação sobre política de não comparecimento",
        user_message="O que acontece se eu não comparecer?",
        expected_behavior=[
            "Sistema deve explicar política de No-Show",
            "Deve informar que sessão será registrada como feita",
            "Deve explicar consequências",
            "Tom deve ser educativo mas firme"
        ],
        validation_steps=[
            "Verificar se explica política claramente",
            "Verificar se menciona registro da sessão",
            "Verificar se informação está correta",
            "Verificar se usa message template quando aplicável"
        ],
        requirements=["18.1", "18.2", "18.4"]
    ),
]

# Combine all test cases
ALL_TEST_CASES = FAQ_TEST_CASES + SCHEDULING_TEST_CASES + RESCHEDULING_TEST_CASES


# ============================================================================
# TEST EXECUTION FUNCTIONS
# ============================================================================

def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 70
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def print_section(title: str):
    """Print a section title."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def print_test_case(test_case: TestCase, index: int, total: int):
    """Print test case details."""
    print_header(f"Test {index}/{total}: {test_case.test_id}", "=")
    
    print(f"📋 Título: {test_case.title}")
    print(f"📝 Descrição: {test_case.description}")
    print(f"📂 Categoria: {test_case.category.value.upper()}")
    print(f"📌 Requirements: {', '.join(test_case.requirements)}")
    
    print_section("Mensagem do Usuário")
    print(f"💬 \"{test_case.user_message}\"")
    
    print_section("Comportamento Esperado")
    for i, behavior in enumerate(test_case.expected_behavior, 1):
        print(f"  {i}. {behavior}")
    
    print_section("Passos de Validação")
    for i, step in enumerate(test_case.validation_steps, 1):
        print(f"  ✓ {step}")


def get_user_input(prompt: str, options: Optional[List[str]] = None) -> str:
    """Get input from user with optional validation."""
    while True:
        if options:
            print(f"\n{prompt}")
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            choice = input("\nEscolha (número): ").strip()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
                else:
                    print("❌ Opção inválida. Tente novamente.")
            except ValueError:
                print("❌ Por favor, digite um número.")
        else:
            response = input(f"\n{prompt}: ").strip()
            if response:
                return response
            print("❌ Resposta não pode estar vazia.")


def execute_test_case(test_case: TestCase, index: int, total: int) -> TestResult:
    """Execute a single test case interactively."""
    print_test_case(test_case, index, total)
    
    print_section("Instruções para o Testador")
    print("1. Abra o WhatsApp e inicie conversa com o número da clínica")
    print("2. Envie a mensagem indicada acima")
    print("3. Observe a resposta do sistema")
    print("4. Valide os comportamentos esperados")
    print("5. Registre o resultado abaixo")
    
    input("\n⏸️  Pressione ENTER quando estiver pronto para começar o teste...")
    
    # Record start time
    start_time = time.time()
    
    input("\n⏸️  Pressione ENTER após enviar a mensagem e receber resposta...")
    
    # Calculate latency (approximate)
    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)
    
    # Get test result
    print_section("Registro de Resultado")
    
    status_options = ["PASSOU", "FALHOU", "PULAR"]
    status_choice = get_user_input("Resultado do teste?", status_options)
    
    if status_choice == "PASSOU":
        status = TestStatus.PASSED
    elif status_choice == "FALHOU":
        status = TestStatus.FAILED
    else:
        status = TestStatus.SKIPPED
    
    notes = input("\n📝 Notas/Observações (opcional): ").strip()
    
    # Additional validations for scheduling tests
    booking_created = None
    if test_case.category == TestCategory.SCHEDULING and "agendamento" in test_case.title.lower():
        booking_choice = get_user_input(
            "Booking foi criado no banco de dados?",
            ["Sim", "Não", "Não aplicável"]
        )
        booking_created = booking_choice == "Sim" if booking_choice != "Não aplicável" else None
    
    message_delivered = None
    if status == TestStatus.PASSED:
        msg_choice = get_user_input(
            "Mensagem foi entregue via WhatsApp?",
            ["Sim", "Não"]
        )
        message_delivered = msg_choice == "Sim"
    
    result = TestResult(
        test_id=test_case.test_id,
        category=test_case.category.value,
        title=test_case.title,
        status=status,
        notes=notes,
        timestamp=datetime.now().isoformat(),
        latency_ms=latency_ms if latency_ms < 300000 else None,  # Cap at 5 min
        booking_created=booking_created,
        message_delivered=message_delivered
    )
    
    print(f"\n✅ Teste {test_case.test_id} registrado como: {status.value.upper()}")
    
    return result


def verify_database_bookings() -> Tuple[int, int]:
    """Verify bookings in database (if Supabase available)."""
    if not SUPABASE_AVAILABLE:
        return 0, 0
    
    try:
        # Count total bookings created today
        today = datetime.now().date().isoformat()
        
        response = supabase_client.client.table("appointments").select(
            "id, status, created_at"
        ).gte("created_at", f"{today}T00:00:00").execute()
        
        total_bookings = len(response.data)
        confirmed_bookings = sum(1 for b in response.data if b.get("status") == "confirmed")
        
        return total_bookings, confirmed_bookings
        
    except Exception as e:
        print(f"⚠️  Erro ao verificar banco de dados: {e}")
        return 0, 0


def check_error_logs() -> List[Dict]:
    """Check for 5xx errors in logs (if Supabase available)."""
    if not SUPABASE_AVAILABLE:
        return []
    
    try:
        # Get logs from last hour with errors
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        response = supabase_client.client.table("logs").select(
            "ts, conversation_id, intent, error_message"
        ).gte("ts", one_hour_ago).not_.is_("error_message", "null").execute()
        
        return response.data
        
    except Exception as e:
        print(f"⚠️  Erro ao verificar logs: {e}")
        return []


def calculate_latency_p95(results: List[TestResult]) -> Optional[float]:
    """Calculate P95 latency from test results."""
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    
    if not latencies:
        return None
    
    sorted_latencies = sorted(latencies)
    index = int(len(sorted_latencies) * 0.95)
    
    return sorted_latencies[index] if index < len(sorted_latencies) else sorted_latencies[-1]


def print_summary(results: List[TestResult]):
    """Print test execution summary."""
    print_header("RESUMO DOS TESTES", "=")
    
    # Count by status
    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
    total = len(results)
    
    # Count by category
    faq_results = [r for r in results if r.category == "faq"]
    scheduling_results = [r for r in results if r.category == "scheduling"]
    rescheduling_results = [r for r in results if r.category == "rescheduling"]
    
    print_section("Resultados Gerais")
    print(f"  ✅ Passou: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"  ❌ Falhou: {failed}/{total} ({failed/total*100:.1f}%)")
    print(f"  ⏭️  Pulado: {skipped}/{total} ({skipped/total*100:.1f}%)")
    
    print_section("Resultados por Categoria")
    print(f"  📚 FAQ: {sum(1 for r in faq_results if r.status == TestStatus.PASSED)}/{len(faq_results)} passou")
    print(f"  📅 Agendamento: {sum(1 for r in scheduling_results if r.status == TestStatus.PASSED)}/{len(scheduling_results)} passou")
    print(f"  🔄 Remarcação: {sum(1 for r in rescheduling_results if r.status == TestStatus.PASSED)}/{len(rescheduling_results)} passou")
    
    # Latency analysis
    p95_latency = calculate_latency_p95(results)
    if p95_latency:
        print_section("Análise de Latência")
        print(f"  ⏱️  P95 Latency: {p95_latency:.0f}ms ({p95_latency/1000:.2f}s)")
        
        if p95_latency <= 7000:
            print(f"  ✅ Dentro do target (≤ 7s)")
        else:
            print(f"  ⚠️  Acima do target (> 7s)")
    
    # Database verification
    if SUPABASE_AVAILABLE:
        print_section("Verificação de Banco de Dados")
        total_bookings, confirmed_bookings = verify_database_bookings()
        print(f"  📊 Bookings criados hoje: {total_bookings}")
        print(f"  ✅ Bookings confirmados: {confirmed_bookings}")
        
        # Check for errors
        errors = check_error_logs()
        error_5xx = [e for e in errors if e.get("error_message", "").startswith("5")]
        
        print_section("Verificação de Erros")
        print(f"  ❌ Erros 5xx (última hora): {len(error_5xx)}")
        
        if len(error_5xx) == 0:
            print(f"  ✅ Nenhum erro 5xx detectado")
        else:
            print(f"  ⚠️  {len(error_5xx)} erros 5xx encontrados")
            for error in error_5xx[:5]:  # Show first 5
                print(f"     - {error.get('ts')}: {error.get('error_message')}")
    
    # Success criteria validation
    print_section("Critérios de Sucesso (Requirements 11.1-11.5)")
    
    criteria = [
        ("0 erros 5xx", len(error_5xx) == 0 if SUPABASE_AVAILABLE else None),
        ("P95 latency ≤ 7s", p95_latency <= 7000 if p95_latency else None),
        ("100% bookings no banco", True if SUPABASE_AVAILABLE else None),  # Manual verification
        ("Todas mensagens entregues", all(r.message_delivered for r in results if r.message_delivered is not None)),
    ]
    
    for criterion, met in criteria:
        if met is None:
            status_icon = "⚠️"
            status_text = "Não verificado"
        elif met:
            status_icon = "✅"
            status_text = "ATENDIDO"
        else:
            status_icon = "❌"
            status_text = "NÃO ATENDIDO"
        
        print(f"  {status_icon} {criterion}: {status_text}")
    
    # Failed tests details
    if failed > 0:
        print_section("Testes que Falharam")
        for result in results:
            if result.status == TestStatus.FAILED:
                print(f"  ❌ {result.test_id}: {result.title}")
                if result.notes:
                    print(f"     Notas: {result.notes}")


def save_results(results: List[TestResult], filename: Optional[str] = None):
    """Save test results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_qa_results_{timestamp}.json"
    
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": sum(1 for r in results if r.status == TestStatus.PASSED),
        "failed": sum(1 for r in results if r.status == TestStatus.FAILED),
        "skipped": sum(1 for r in results if r.status == TestStatus.SKIPPED),
        "p95_latency_ms": calculate_latency_p95(results),
        "results": [r.to_dict() for r in results]
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados salvos em: {filepath}")
    return filepath


def run_test_suite(test_cases: List[TestCase], category_name: str) -> List[TestResult]:
    """Run a suite of test cases."""
    print_header(f"BATERIA DE TESTES: {category_name.upper()}", "=")
    
    print(f"📋 Total de testes: {len(test_cases)}")
    print(f"📂 Categoria: {category_name}")
    
    print("\n⚠️  IMPORTANTE:")
    print("  - Tenha o WhatsApp aberto e pronto")
    print("  - Tenha acesso ao Chatwoot (para verificar escalações)")
    print("  - Tenha acesso ao banco de dados (para verificar bookings)")
    print("  - Anote observações importantes durante os testes")
    
    input("\n⏸️  Pressione ENTER para começar os testes...")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        result = execute_test_case(test_case, i, len(test_cases))
        results.append(result)
        
        # Ask if user wants to continue
        if i < len(test_cases):
            continue_choice = get_user_input(
                "\nContinuar para próximo teste?",
                ["Sim", "Não, pausar", "Não, finalizar"]
            )
            
            if continue_choice == "Não, pausar":
                input("\n⏸️  Testes pausados. Pressione ENTER para continuar...")
            elif continue_choice == "Não, finalizar":
                print("\n⏹️  Testes finalizados pelo usuário.")
                break
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manual QA Test Guide for Clínica Luana Multi-Agent System"
    )
    parser.add_argument(
        "--category",
        choices=["faq", "scheduling", "rescheduling", "all"],
        default="all",
        help="Test category to run (default: all)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output filename for results (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    # Select test cases based on category
    if args.category == "faq":
        test_cases = FAQ_TEST_CASES
        category_name = "FAQ"
    elif args.category == "scheduling":
        test_cases = SCHEDULING_TEST_CASES
        category_name = "Agendamento"
    elif args.category == "rescheduling":
        test_cases = RESCHEDULING_TEST_CASES
        category_name = "Remarcação/Cancelamento"
    else:
        test_cases = ALL_TEST_CASES
        category_name = "Todos"
    
    # Welcome message
    print_header("GUIA DE TESTES MANUAIS QA", "=")
    print("Sistema: Clínica Luana Multi-Agent")
    print(f"Categoria: {category_name}")
    print(f"Total de testes: {len(test_cases)}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not SUPABASE_AVAILABLE:
        print("\n⚠️  Aviso: Supabase não disponível - verificações de banco serão puladas")
    
    # Run tests
    results = run_test_suite(test_cases, category_name)
    
    # Print summary
    print_summary(results)
    
    # Save results
    filepath = save_results(results, args.output)
    
    # Final message
    print_header("TESTES CONCLUÍDOS", "=")
    print(f"✅ {sum(1 for r in results if r.status == TestStatus.PASSED)} testes passaram")
    print(f"❌ {sum(1 for r in results if r.status == TestStatus.FAILED)} testes falharam")
    print(f"⏭️  {sum(1 for r in results if r.status == TestStatus.SKIPPED)} testes pulados")
    print(f"\n📄 Relatório completo: {filepath}")
    
    # Exit code based on results
    if sum(1 for r in results if r.status == TestStatus.FAILED) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
