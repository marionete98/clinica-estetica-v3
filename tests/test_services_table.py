"""
Teste mínimo para verificar tabela services
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env')

async def test_services_table():
    """Testa se consegue acessar a tabela services"""
    try:
        from config.supabase_client import supabase_client

        # Teste simples - listar serviços ativos
        supabase = supabase_client.client

        def _fetch_services():
            return supabase.table("services").select("id, name, active").eq("active", True).limit(3).execute()

        response = await asyncio.to_thread(_fetch_services)

        if response.data:
            print(f"✅ Tabela 'services' existe! Encontrados {len(response.data)} serviços:")
            for service in response.data:
                print(f"  - {service['name']} (ID: {service['id']})")
            return True
        else:
            print("❌ Tabela 'services' não retornou dados")
            return False

    except Exception as e:
        print(f"❌ Erro ao acessar tabela services: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_services_table())
