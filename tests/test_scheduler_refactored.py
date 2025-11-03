"""
Teste para validar refatoração do scheduler_tools.py
Valida integração com Calendar API
"""
import asyncio
from datetime import datetime, timedelta

async def test_scheduler_refactored():
    """Testa scheduler refatorado com Calendar API"""
    from tools.scheduler_tools import list_available_slots, create_booking
    from models.repository import get_contact_by_phone, create_or_update_contact
    
    print("=" * 60)
    print("TESTE: Scheduler Refatorado com Calendar API")
    print("=" * 60)
    
    # Test 1: list_available_slots com procedure_name
    print("\n1️⃣ Testando list_available_slots...")
    try:
        slots = await list_available_slots(
            procedure_name="Botox Facial",
            duration_min=30,
            date_range=7
        )
        print(f"✅ list_available_slots funcionou!")
        print(f"   Encontrados {len(slots)} slots disponíveis")
        if slots:
            print(f"   Exemplo: {slots[0]['date']} às {slots[0]['start_time']}")
    except Exception as e:
        print(f"❌ Erro em list_available_slots: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: create_booking com novos parâmetros
    print("\n2️⃣ Testando create_booking...")
    try:
        # Criar ou buscar contato de teste
        # Formato brasileiro: (94) 99139-8585 ou 94991398585
        test_phone = "94991398585"
        contact = await get_contact_by_phone(test_phone)
        
        if not contact:
            print("   Criando contato de teste...")
            contact = await create_or_update_contact(
                phone=test_phone,
                name="Teste Scheduler",
                email="teste@scheduler.com"
            )
        
        print(f"   Contato: {contact.name} ({contact.phone})")
        
        # Agendar para daqui a 2 dias às 14h
        start_dt = datetime.now() + timedelta(days=2)
        start_dt = start_dt.replace(hour=14, minute=0, second=0, microsecond=0)
        
        booking = await create_booking(
            contact_id=str(contact.id),
            procedure_name="Botox Facial",
            treatment_category="Harmonização facial",
            duration_min=30,
            start_datetime=start_dt.isoformat(),
            room="Sala 02",
            conversation_id="test_refactored"
        )
        
        print(f"✅ create_booking funcionou!")
        print(f"   Booking ID: {booking['booking_id']}")
        print(f"   Calendar ID: {booking['calendar_appointment_id']}")
        print(f"   Procedimento: {booking['procedure']}")
        print(f"   Tratamento: {booking['treatment']}")
        print(f"   Status: {booking['status']}")
        print(f"   Data: {booking['start_datetime']}")
        
    except Exception as e:
        print(f"❌ Erro em create_booking: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Validar estrutura de resposta
    print("\n3️⃣ Validando estrutura de resposta...")
    try:
        if 'booking' in locals():
            required_fields = [
                'booking_id', 'calendar_appointment_id', 'contact_id',
                'start_datetime', 'end_datetime', 'status',
                'client_name', 'client_phone', 'procedure', 'treatment'
            ]
            
            missing = [f for f in required_fields if f not in booking]
            if missing:
                print(f"❌ Campos faltando: {missing}")
            else:
                print(f"✅ Todos os campos obrigatórios presentes!")
                
            # Validar tipos
            assert isinstance(booking['procedure'], str), "procedure deve ser string"
            assert isinstance(booking['treatment'], str), "treatment deve ser string"
            assert booking['status'] == 'scheduled', "status deve ser 'scheduled'"
            print(f"✅ Tipos de dados corretos!")
        else:
            print("⚠️ Booking não foi criado, pulando validação")
            
    except AssertionError as e:
        print(f"❌ Validação falhou: {e}")
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scheduler_refactored())
