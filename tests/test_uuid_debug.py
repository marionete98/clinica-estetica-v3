"""
Teste específico para verificar o erro do UUID no scheduler
"""
import asyncio
from uuid import UUID

async def test_uuid_issue():
    """Testa especificamente o problema do UUID"""
    from tools.scheduler_tools import list_available_slots

    service_id = "659ee29a-ce0c-47a8-9f73-a56a02de137e"
    print(f"Testando com service_id: {service_id}")

    try:
        # Testar se o UUID é válido
        uuid_obj = UUID(service_id)
        print(f"✅ UUID válido: {uuid_obj}")

        # Tentar chamar a função
        slots = await list_available_slots(
            service_id=service_id,
            date_range=7
        )
        print(f"✅ Função executou com sucesso! Retornou {len(slots)} slots")
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        print(f"Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_uuid_issue())
