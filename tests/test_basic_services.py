"""
Teste mínimo para verificar se a tabela services existe e é acessível
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env')

async def test_basic_services():
    """Teste básico da tabela services"""
    try:
        from config.supabase_client import supabase_client

        supabase = supabase_client.client

        print("🔍 Testando consulta básica na tabela 'services'...")

        def _test_query():
            # Consulta simples - apenas verificar se a tabela existe
            return supabase.table("services").select("id").limit(1).execute()

        response = await asyncio.to_thread(_test_query)

        if response.data is not None:
            print(f"✅ Tabela 'services' existe e é acessível!")
            print(f"   Dados retornados: {len(response.data)} registros")
            return True
        else:
            print("❌ Consulta retornou dados nulos")
            return False

    except Exception as e:
        print(f"❌ Erro na consulta básica: {e}")
        print(f"   Tipo: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_basic_services())
