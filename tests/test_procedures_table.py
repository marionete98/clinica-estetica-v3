"""
Verificar se existe tabela 'procedures' ao invés de 'services'
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env')

async def test_procedures_table():
    """Testa se a tabela é 'procedures' ao invés de 'services'"""
    try:
        from config.supabase_client import supabase_client

        supabase = supabase_client.client

        # Testar tabela 'procedures' (mais provável)
        def _fetch_procedures():
            return supabase.table("procedures").select("id, name, active").eq("active", True).limit(5).execute()

        response = await asyncio.to_thread(_fetch_procedures)

        if response.data:
            print(f"✅ Tabela 'procedures' existe! Encontrados {len(response.data)} procedimentos:")
            for procedure in response.data:
                print(f"  - {procedure['name']} (ID: {procedure['id']})")
                print(f"    UUID válido? {procedure['id']}")
            return True
        else:
            print("❌ Tabela 'procedures' não retornou dados")
            return False

    except Exception as e:
        print(f"❌ Erro ao acessar tabela procedures: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_procedures_table())
