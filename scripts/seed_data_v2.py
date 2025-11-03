"""
Seed script for Clínica Luana database (v2 - adapted for existing schema)
Populates initial data: rooms, procedures, message templates, and knowledge base
Requirements: 5.2, 13.1, 13.2, 13.3, 14.1, 14.2, 15.1, 15.2, 4.2, 4.3
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))

from config.supabase_client import supabase_client


async def seed_rooms():
    """Insert clinic rooms"""
    supabase = supabase_client.client
    
    rooms = [
        {"name": "Sala 01", "description": "Atendimento corporal e facial", "active": True},
        {"name": "Sala 02", "description": "Depilação a laser, atendimentos corporais e faciais", "equipment": "Laser Galaxy Fiber", "active": True},
        {"name": "Sala 03", "description": "Sala para Consulta", "active": True},
        {"name": "Sala 04", "description": "Criolipolise", "equipment": "Criolipolise Medical San", "active": True},
        {"name": "Sala 05", "description": "Sala para Manta térmica", "active": True},
        {"name": "Apartamento", "description": "Para Pós Operatório", "active": True},
        {"name": "Esterilização", "description": "Esterilização de materiais usados na clínica", "active": True},
    ]
    
    print("Seeding rooms...")
    for room in rooms:
        result = supabase.table("rooms").upsert(room, on_conflict="name").execute()
        print(f"  ✓ {room['name']}")
    
    return len(rooms)


async def seed_procedures():
    """Insert clinic procedures"""
    supabase = supabase_client.client
    
    procedures = [
        {
            "name": "Depilação a Laser",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": None,
            "description": "Remoção de pelos com laser Galaxy Fiber. Contraindicações: gravidez, doenças de pele, câncer de pele, pele bronzeada, diabetes. Cuidados: evitar sol por 7 dias, usar FPS 30+. Cancelamento: 24h antecedência.",
            "active": True
        },
        {
            "name": "Harmonização Facial",
            "category": "Facial",
            "duration_minutes": 60,
            "price": None,
            "description": "Ácido Hialurônico, Botox, Lift de Fios, Bioestimuladores. Requer consulta R$ 200 (abatível). Contraindicações: gravidez, lactação, infecções, doenças autoimunes. Cancelamento: 4h antecedência.",
            "active": True
        },
        {
            "name": "Harmonização Corporal",
            "category": "Corporal",
            "duration_minutes": 90,
            "price": None,
            "description": "Tratamento para gordura localizada, flacidez, celulite. Requer consulta R$ 200. Contraindicações: infecções, doenças cardíacas graves, trombose, câncer, diabetes descompensada, gravidez. Cancelamento: 4h antecedência.",
            "active": True
        },
        {
            "name": "Drenagem Linfática",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": 200.00,
            "description": "Massagem para eliminar líquidos e toxinas. Indicações: retenção, inchaço, pós-operatório, celulite. Contraindicações: infecções agudas, trombose, insuficiência cardíaca, problemas renais, câncer ativo.",
            "active": True
        },
        {
            "name": "Massagem Modeladora",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": 200.00,
            "description": "Massagem vigorosa para modelar corpo e reduzir medidas. Contraindicações: gravidez, problemas circulatórios graves.",
            "active": True
        },
        {
            "name": "Diástase",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": None,
            "description": "Tratamento com Criofrequência para fechar diástase até 70%. Melhora flacidez, gordura localizada, dores nas costas, postura. Contraindicações: hipertensão, câncer. Requer consulta.",
            "active": True
        },
        {
            "name": "Criolipólise de Placas",
            "category": "Corporal",
            "duration_minutes": 480,
            "price": None,
            "description": "Redução de gordura localizada por resfriamento controlado. Duração: dia inteiro (8:30-18:00). Contraindicações: gestantes, hérnias, feridas, doenças hepáticas, diabetes descompensado. Requer consulta.",
            "active": True
        },
        {
            "name": "Microfocado",
            "category": "Facial",
            "duration_minutes": 120,
            "price": None,
            "description": "Ultrassom microfocado para flacidez e rejuvenescimento facial. Estimula colágeno e elastina. Contraindicações: gravidez, lactação, doenças de pele, implantes metálicos, queloides. Requer consulta.",
            "active": True
        },
        {
            "name": "Pein (Varizes)",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": None,
            "description": "Tratamento estético para varizes e vasos visíveis. Contraindicações: infecções, feridas, gravidez, lactação, doenças de pele graves, problemas circulatórios. Requer consulta.",
            "active": True
        },
        {
            "name": "Apartamento Pós-Operatório",
            "category": "Pós-Operatório",
            "duration_minutes": 7200,
            "price": 4000.00,
            "description": "Estadia 5 dias com cama, refeições, drenagem, ozonioterapia, retirada de dreno. Requer acompanhante. Taxa banho: R$ 500. Cancelamento: 48h antecedência.",
            "active": True
        },
        {
            "name": "Laser Lavieen",
            "category": "Facial",
            "duration_minutes": 40,
            "price": None,
            "description": "BB Glow avançado para rejuvenescimento, manchas, flacidez, melasma, cicatrizes de acne, clareamento. Avaliação GRATUITA. Contraindicações: gravidez, lactação, infecções, câncer de pele.",
            "active": True
        },
        {
            "name": "Lipo de Papada",
            "category": "Facial",
            "duration_minutes": 120,
            "price": 4500.00,
            "description": "Remoção de gordura submentoniana. Promoção: R$ 4.500 (de R$ 5.500). Pacote com 10 drenagens: R$ 5.500. Contraindicações: gravidez, lactação, infecções, coagulação. Cancelamento: 48h.",
            "active": True
        },
        {
            "name": "Endolaser",
            "category": "Corporal",
            "duration_minutes": 120,
            "price": None,
            "description": "Tratamento minimamente invasivo para gordura localizada e flacidez subcutânea. Contraindicações: gravidez, lactação, infecções, problemas circulatórios. Requer consulta. Cancelamento: 48h.",
            "active": True
        },
        {
            "name": "Camuflagem de Cicatriz e Estrias",
            "category": "Corporal",
            "duration_minutes": 90,
            "price": None,
            "description": "Disfarce de cicatrizes e estrias com uniformização visual. Contraindicações: infecções, gravidez, lactação, queloides, coagulação, fotossensibilizantes, alergias. Requer consulta.",
            "active": True
        },
        {
            "name": "Reconstrução de Aréola",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": None,
            "description": "Restauração de aréolas pós-mastectomia ou lesões. Contraindicações: infecções, doenças autoimunes, alergia a pigmentos, gravidez, lactação, imunossupressão. Requer consulta.",
            "active": True
        },
    ]
    
    print("\nSeeding procedures...")
    for proc in procedures:
        result = supabase.table("procedures").upsert(proc, on_conflict="name").execute()
        print(f"  ✓ {proc['name']}")
    
    return len(procedures)


async def seed_knowledge_base():
    """Insert knowledge base articles"""
    supabase = supabase_client.client
    
    kb_articles = [
        {
            "category": "general",
            "title": "Informações Gerais da Clínica",
            "content": """Luana Carla Dermo Clinic
Endereço: Rua José Pereira Costa, 540, Centro, Canaã dos Carajás, PA, 68350-065
Telefone: (94) 99139-8585
Email: luanacarla.smendes@gmail.com

Horários:
- Segunda a Sexta: 08:30 - 19:00
- Sábado: 08:30 - 12:00
- Domingo: Fechado

Agendamento: mínimo 1 hora de antecedência
Intervalo entre procedimentos: 10 minutos""",
            "importance": 10,
            "status": "active"
        },
        {
            "category": "policy",
            "title": "Política de Cancelamento",
            "content": """Harmonização (Facial/Corporal): cancelar até 4h antes
Depilação a Laser: cancelar até 24h antes
Outros procedimentos: cancelar até 24h antes

Reagendamento: permitido até 2 vezes com aviso de 4h

No-Show: sem aviso, cliente perde direito ao reagendamento e sessão é registrada como feita""",
            "importance": 10,
            "status": "active"
        },
        {
            "category": "treatment",
            "subcategory": "laser",
            "title": "Depilação a Laser",
            "content": """Método com laser Galaxy Fiber para destruir folículos pilosos. Reduz crescimento permanentemente.

Duração: 60 minutos
Sala: Sala 02

Contraindicações: gravidez, doenças de pele, câncer de pele, pele bronzeada/queimada, diabetes

Cuidados pós-tratamento:
- Evitar sol por 7 dias
- Usar FPS 30+
- Hidratar pele
- Não usar produtos irritantes
- Bronzeamento só após 15 dias

Cancelamento: 24h antecedência""",
            "importance": 9,
            "status": "active"
        },
        {
            "category": "treatment",
            "subcategory": "facial",
            "title": "Harmonização Facial",
            "content": """Procedimentos: Ácido Hialurônico, Botox, Lift de Fios, Bioestimuladores de Colágeno

Duração: 60 minutos
Consulta: R$ 200 (abatível no tratamento)
Agendamento consulta: 30% antecipado

Indicações: rejuvenescimento, rugas, simetria, volume, flacidez

Contraindicações: gravidez, lactação, infecções, doenças autoimunes, alergias, doenças neuromusculares, câncer

Cancelamento: 4h antecedência""",
            "importance": 9,
            "status": "active"
        },
        {
            "category": "treatment",
            "subcategory": "corporal",
            "title": "Drenagem Linfática",
            "content": """Massagem suave para eliminar líquidos e toxinas

Duração: 60 minutos
Preço: R$ 200

Indicações: retenção de líquidos, inchaço, edema, pós-operatório, celulite, linfedema, má circulação, gravidez (após 3 meses)

Contraindicações: infecções agudas, trombose venosa profunda, insuficiência cardíaca descompensada, problemas renais graves, câncer ativo (sem autorização médica)

Cuidados: beber bastante água, alimentação leve e saudável

Cancelamento: 24h antecedência""",
            "importance": 8,
            "status": "active"
        },
        {
            "category": "service",
            "subcategory": "pos_operatorio",
            "title": "Apartamento Pós-Operatório",
            "content": """Estadia de 5 dias: R$ 4.000

Incluso:
- Cama confortável com enxoval limpo
- Ambientes climatizados e silenciosos
- Wi-Fi e TV
- Cadeira pós-operatório
- 4 refeições/dia
- Pessoa à disposição (8h-19h fim de semana)
- Drenagem pós-operatório manual
- Ozonioterapia (se necessário)
- Retirada de dreno (3 dias)

Observações:
- Requer acompanhante
- Taxa banho (com acompanhante): R$ 500

Cancelamento: 48h antecedência""",
            "importance": 8,
            "status": "active"
        },
        {
            "category": "service",
            "subcategory": "emagrecimento",
            "title": "Tratamento Mounjaro (Tirzepatida)",
            "content": """Tratamento com Tirzepatida para perda de peso

Consulta: R$ 280 (isento se fechar tratamento em 24h)
Agendamento: 50% antecipado

Plano Redesign Start: R$ 1.700 ou 6x R$ 316
- 4 doses Tirzepatida 2,5mg
- 1 Imunitbooster
- 1 detox injetável
- Bioimpedância
- Acompanhamento semanal 30 dias
- Plano alimentar

Plano Redesign Power: R$ 3.499 ou 10x R$ 370
- Tudo do Start +
- Biorressonância
- 4 sessões Detox Power
- 1 kit detox 15 dias

Valores dependem do biotipo individual""",
            "importance": 7,
            "status": "active"
        },
        {
            "category": "service",
            "title": "Laser Lavieen - BB Glow",
            "content": """BB Glow avançado para rejuvenescimento

Duração: 30-40 minutos
Avaliação: GRATUITA
Valores: mediante consulta

Indicações: envelhecimento, flacidez, manchas, hiperpigmentação, cicatrizes de acne, poros dilatados, melasma, clareamento (virilha, axilas), manchas corporais

Contraindicações: gravidez, lactação, infecções, câncer de pele

Cuidados: proteção solar rigorosa, hidratação""",
            "importance": 7,
            "status": "active"
        },
        {
            "category": "service",
            "title": "Lipo de Papada",
            "content": """Remoção de gordura abaixo do queixo

Duração: 2 horas
Preço: R$ 4.500 (promoção de R$ 5.500)
Parcelamento: 10x sem juros

Pacote com pós: R$ 5.500 (lipo + 10 drenagens)

Contraindicações: gravidez, lactação, infecções, problemas de coagulação

Cuidados: cinta, drenagem linfática, repouso

Cancelamento: 48h antecedência""",
            "importance": 7,
            "status": "active"
        },
        {
            "category": "service",
            "title": "Locação de Poltronas Pós-Operatório",
            "content": """Poltrona reclinável para recuperação

Preços:
- 1 dia: R$ 150
- 5 dias: R$ 625
- 10 dias: R$ 1.100
- 15 dias: R$ 1.500

Frete:
- Canaã dos Carajás: R$ 100
- Parauapebas e região: consultar

Benefícios: posicionamento ajustável, suporte ergonômico, facilidade de movimentação, conforto, sono adequado""",
            "importance": 6,
            "status": "active"
        },
        {
            "category": "service",
            "title": "Pacotes Pós-Operatório Corporal",
            "content": """Acompanhamento profissional pós-cirurgia plástica

Pacotes:
- 5 sessões: R$ 1.500 ou 10x R$ 164,80
- 10 sessões: R$ 2.500 ou 10x R$ 274,67
- 20 sessões: R$ 3.500 ou 10x R$ 384,53

Inclui: drenagem linfática manual, terapias específicas, acompanhamento da evolução, técnicas modernas

Valor independe de associações""",
            "importance": 6,
            "status": "active"
        },
        {
            "category": "service",
            "title": "Cuidados Pós-Cirurgias Faciais",
            "content": """Retirada/limpeza de curativo, ledterapia, terapias manuais

Preços:
- 1 sessão: R$ 250
- 2 sessões: R$ 400
- 5 sessões: R$ 800 (nariz/blefaroplastia)
- 10 sessões: R$ 1.200 (lipo papada)
- 10 sessões: R$ 1.800 (cirurgia dupla/tripla com lifting)

Parcelamento: consultar taxa""",
            "importance": 6,
            "status": "active"
        },
        {
            "category": "consultation",
            "title": "Tipos de Consultas",
            "content": """1. Harmonização (Luana):
   R$ 200 (abatível no tratamento)
   Inclui: exame imediato, prescrições personalizadas
   Agendamento: 30% antecipado

2. Mounjaro:
   R$ 280 (isento se fechar em 24h)
   Inclui: avaliação fisiológica, orientação nutricional, biorressonância, bioimpedância
   Agendamento: 50% antecipado

3. Biomédica (Dra. Lourrany):
   R$ 150 (abatível em tratamentos com ela)
   Agendamento: 50% antecipado

4. Laser Lavieen:
   GRATUITA""",
            "importance": 9,
            "status": "active"
        },
    ]
    
    print("\nSeeding knowledge base...")
    for article in kb_articles:
        # Check if article exists by title
        existing = supabase.table("knowledge_base").select("id").eq("title", article["title"]).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table("knowledge_base").update(article).eq("title", article["title"]).execute()
            print(f"  ↻ {article['title']}")
        else:
            # Insert new
            result = supabase.table("knowledge_base").insert(article).execute()
            print(f"  ✓ {article['title']}")
    
    return len(kb_articles)


async def main():
    """Main seed function"""
    print("=" * 60)
    print("CLÍNICA LUANA - DATABASE SEED SCRIPT V2")
    print("=" * 60)
    
    try:
        rooms_count = await seed_rooms()
        procedures_count = await seed_procedures()
        kb_count = await seed_knowledge_base()
        
        print("\n" + "=" * 60)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  • {rooms_count} rooms")
        print(f"  • {procedures_count} procedures")
        print(f"  • {kb_count} knowledge base articles")
        print("\nNext steps:")
        print("  1. Verify data in Supabase dashboard")
        print("  2. Test FAQ agent with knowledge base queries")
        print("  3. Test scheduler agent with procedure availability")
        
    except Exception as e:
        print(f"\n❌ ERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
