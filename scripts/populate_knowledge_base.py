#!/usr/bin/env python3
"""
Script to populate/update knowledge base with clinic information.
This script helps maintain the FAQ knowledge base without touching code.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.supabase_client import supabase_client
from datetime import datetime


class KnowledgeBaseManager:
    """Manages knowledge base entries for the FAQ agent."""
    
    def __init__(self):
        self.supabase = supabase_client.client
    
    async def add_entry(
        self,
        category: str,
        subcategory: str,
        title: str,
        content: str,
        importance: int = 5,
        source: str = "manual"
    ):
        """Add a new knowledge base entry."""
        try:
            result = self.supabase.table("knowledge_base").insert({
                "category": category,
                "subcategory": subcategory,
                "title": title,
                "content": content,
                "importance": importance,
                "source": source,
                "status": "active",
                "search_text": f"{title} {content}".lower()
            }).execute()
            
            print(f"✅ Added: {title}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Error adding {title}: {e}")
            return None
    
    async def update_entry(self, entry_id: str, **updates):
        """Update an existing knowledge base entry."""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("knowledge_base").update(updates).eq("id", entry_id).execute()
            
            print(f"✅ Updated entry: {entry_id}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Error updating {entry_id}: {e}")
            return None
    
    async def search_entries(self, query: str, category: str = None):
        """Search knowledge base entries."""
        try:
            query_builder = self.supabase.table("knowledge_base").select("*")
            
            if category:
                query_builder = query_builder.eq("category", category)
            
            if query:
                query_builder = query_builder.ilike("search_text", f"%{query.lower()}%")
            
            result = query_builder.execute()
            return result.data
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    async def list_categories(self):
        """List all categories in knowledge base."""
        try:
            result = self.supabase.table("knowledge_base").select("category, subcategory").execute()
            
            categories = {}
            for item in result.data:
                cat = item["category"]
                subcat = item["subcategory"]
                
                if cat not in categories:
                    categories[cat] = set()
                
                if subcat:
                    categories[cat].add(subcat)
            
            return {k: list(v) for k, v in categories.items()}
            
        except Exception as e:
            print(f"❌ Error listing categories: {e}")
            return {}
    
    async def bulk_add_treatments(self):
        """Add common treatment information to knowledge base."""
        treatments = [
            {
                "category": "Tratamentos",
                "subcategory": "Depilação",
                "title": "Depilação a Laser - Informações Gerais",
                "content": """Tecnologia: Laser Galaxy Fiber (tecnologia de ponta)
Áreas: Todas as regiões do corpo
Duração: Varia por área (15-60 minutos)
Sessões: Geralmente 6-10 sessões para resultado completo
Intervalo: 30-45 dias entre sessões
Preço: Sob consulta (varia por área)
Avaliação: Gratuita
Política de cancelamento: 24 horas de antecedência""",
                "importance": 9
            },
            {
                "category": "Tratamentos",
                "subcategory": "Depilação",
                "title": "Depilação a Laser - Contraindicações",
                "content": """Contraindicações para depilação a laser:
- Gravidez
- Pele bronzeada recentemente
- Uso de isotretinoína
- Infecções ativas na pele
- Histórico de queloides
- Uso de medicamentos fotossensibilizantes""",
                "importance": 10
            },
            {
                "category": "Tratamentos",
                "subcategory": "Depilação",
                "title": "Depilação a Laser - Cuidados Pós-Tratamento",
                "content": """Cuidados após depilação a laser:
- Evitar exposição solar por 7 dias
- Usar protetor solar FPS 30+ diariamente
- Hidratar bem a pele
- Não usar lâmina entre sessões (apenas cera ou pinça)
- Evitar sauna e exercícios intensos por 24h
- Não usar produtos com ácidos por 48h""",
                "importance": 9
            },
            {
                "category": "Tratamentos",
                "subcategory": "Harmonização",
                "title": "Harmonização Facial - Informações Gerais",
                "content": """Procedimentos: Botox, preenchimentos labiais, preenchimento de olheiras, bioestimuladores de colágeno
Consulta: R$ 200 (valor pode ser abatido no tratamento)
Duração: 30-60 minutos por procedimento
Resultados: Imediatos para preenchimentos, 7-14 dias para botox
Durabilidade: 6-18 meses dependendo do procedimento
Política de cancelamento: 4 horas de antecedência""",
                "importance": 9
            },
            {
                "category": "Tratamentos",
                "subcategory": "Harmonização",
                "title": "Harmonização Facial - Contraindicações",
                "content": """Contraindicações para harmonização facial:
- Gravidez
- Amamentação
- Doenças neuromusculares
- Alergia à toxina botulínica
- Infecções na área de aplicação
- Uso de anticoagulantes
- Histórico de queloides""",
                "importance": 10
            },
            {
                "category": "Tratamentos",
                "subcategory": "Harmonização",
                "title": "Harmonização Facial - Cuidados Pós-Tratamento",
                "content": """Cuidados após harmonização facial:
- Não deitar por 4 horas após botox
- Evitar exercícios intensos por 24h
- Não massagear área tratada
- Evitar calor excessivo (sauna, sol) por 48h
- Não fazer expressões exageradas por 24h
- Evitar álcool por 24h""",
                "importance": 9
            },
            {
                "category": "Tratamentos",
                "subcategory": "Corporal",
                "title": "Criolipólise - Informações Gerais",
                "content": """Como funciona: Congela e elimina células de gordura localizada de forma não invasiva
Sessões: Geralmente 1-3 sessões por área
Intervalo: 60-90 dias entre sessões
Resultados: Visíveis em 30-90 dias
Áreas tratadas: Abdômen, flancos, coxas, braços
Preço: Sob consulta (varia por área e número de aplicadores)
Avaliação: Gratuita para orçamento personalizado""",
                "importance": 8
            },
            {
                "category": "Tratamentos",
                "subcategory": "Corporal",
                "title": "Criolipólise - Contraindicações",
                "content": """Contraindicações para criolipólise:
- Gravidez
- Crioglobulinemia
- Urticária ao frio
- Hérnias na área de tratamento
- Dermatite ou eczema na área
- Neuropatia periférica""",
                "importance": 10
            }
        ]
        
        print("🔄 Adding treatment information...")
        for treatment in treatments:
            await self.add_entry(**treatment)
        
        print(f"✅ Added {len(treatments)} treatment entries")
    
    async def bulk_add_policies(self):
        """Add policy information to knowledge base."""
        policies = [
            {
                "category": "Políticas",
                "subcategory": "Agendamento",
                "title": "Antecedência Mínima para Agendamento",
                "content": "Antecedência mínima: 1 hora do horário atual para garantir preparação adequada",
                "importance": 10
            },
            {
                "category": "Políticas",
                "subcategory": "Agendamento",
                "title": "Política de Remarcações",
                "content": "Máximo de 2 remarcações por agendamento. Após atingir o limite, é necessário contato direto com a clínica pelo telefone (94) 99139-8585",
                "importance": 10
            },
            {
                "category": "Políticas",
                "subcategory": "Cancelamento",
                "title": "Política de Cancelamento - Harmonização",
                "content": "Harmonização facial/corporal: cancelamento deve ser feito com 4 horas de antecedência. Fora do prazo: sessão conta como realizada (no-show)",
                "importance": 10
            },
            {
                "category": "Políticas",
                "subcategory": "Cancelamento",
                "title": "Política de Cancelamento - Depilação Laser",
                "content": "Depilação a laser: cancelamento deve ser feito com 24 horas de antecedência. Fora do prazo: sessão conta como realizada (no-show)",
                "importance": 10
            },
            {
                "category": "Políticas",
                "subcategory": "No-Show",
                "title": "Política de No-Show",
                "content": """Política de falta sem aviso:
- Sessão registrada como realizada
- Impacta histórico do paciente
- Pode afetar futuros agendamentos
- Valor da sessão é cobrado
- Tolerância de atraso: máximo 10 minutos""",
                "importance": 10
            },
            {
                "category": "Políticas",
                "subcategory": "Pagamento",
                "title": "Formas de Pagamento",
                "content": """Formas de pagamento aceitas:
- Dinheiro
- PIX
- Cartão de crédito
- Cartão de débito
- Parcelamento disponível para pacotes
- Consultar condições específicas""",
                "importance": 8
            }
        ]
        
        print("🔄 Adding policy information...")
        for policy in policies:
            await self.add_entry(**policy)
        
        print(f"✅ Added {len(policies)} policy entries")


async def main():
    """Main function with interactive menu."""
    kb = KnowledgeBaseManager()
    
    while True:
        print("\n" + "="*50)
        print("📚 KNOWLEDGE BASE MANAGER")
        print("="*50)
        print("1. List categories")
        print("2. Search entries")
        print("3. Add single entry")
        print("4. Bulk add treatments")
        print("5. Bulk add policies")
        print("6. Exit")
        print("-"*50)
        
        choice = input("Choose option (1-6): ").strip()
        
        if choice == "1":
            print("\n📂 Categories:")
            categories = await kb.list_categories()
            for cat, subcats in categories.items():
                print(f"  {cat}")
                for subcat in subcats:
                    print(f"    └─ {subcat}")
        
        elif choice == "2":
            query = input("Search query: ").strip()
            category = input("Category (optional): ").strip() or None
            
            results = await kb.search_entries(query, category)
            print(f"\n🔍 Found {len(results)} results:")
            for result in results[:10]:  # Show first 10
                print(f"  📄 {result['title']}")
                print(f"     Category: {result['category']}/{result['subcategory']}")
                print(f"     Content: {result['content'][:100]}...")
                print()
        
        elif choice == "3":
            print("\n➕ Add new entry:")
            category = input("Category: ").strip()
            subcategory = input("Subcategory: ").strip()
            title = input("Title: ").strip()
            content = input("Content: ").strip()
            importance = int(input("Importance (1-10): ").strip() or "5")
            
            await kb.add_entry(category, subcategory, title, content, importance)
        
        elif choice == "4":
            await kb.bulk_add_treatments()
        
        elif choice == "5":
            await kb.bulk_add_policies()
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    asyncio.run(main())