"""
⚠️ DEPRECATED - DO NOT USE THIS SCRIPT ⚠️

This seed script is DEPRECATED and currently BROKEN.

PROBLEM:
- Designed for migration schema (supabase/migrations/001_create_initial_schema.sql)
- But uses fields (description, equipment) that don't exist in that schema
- Migration defines rooms with 'room_type' field, not 'description' or 'equipment'
- Targets tables (services, equipment) that may not exist in production

USE INSTEAD:
- scripts/seed_data_v2.py - Properly adapted for existing calendar database

Original purpose: Seed script for Clínica Luana database
Would populate: rooms, equipment, services, message templates, and knowledge base
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
    
    return supabase.table("rooms").select("*").execute().data


async def seed_equipment():
    """Equipment info is now stored in rooms.equipment field"""
    print("\nEquipment information stored in rooms table")
    return {}


async def seed_services():
    """Insert clinic services into procedures table"""
    supabase = supabase_client.client
    
    procedures = [
        {
            "name": "Depilação a Laser",
            "category": "Corporal",
            "duration_minutes": 60,
            "price": None,  # Varies by area
            "description": "A depilação a laser é um método de remoção dos pelos que utiliza feixes de luz concentrada (laser) para destruir os folículos pilosos. É uma técnica eficaz e duradoura, que reduz significativamente o crescimento dos pelos ao longo do tempo. Equipamento: Laser Galaxy Fiber. Contraindicações: Gravidez, doenças de pele, câncer de pele, pele muito bronzeada ou com queimaduras solares e diabetes. Cuidados pós-tratamento: Evitar exposição ao sol por pelo menos 7 dias. Usar protetor solar FPS 30+. Cancelamento: 24h de antecedência.",
            "active": True
        },
        {
            "name": "Harmonização Facial",
            "category": "Facial",
            "duration_minutes": 60,
            "price": None,
            "description": "Ácido Hialurônico, Botox, Lift de Fios, Bioestimuladores de Colágeno. Requer consulta (R$ 200,00 - pode ser abatido no tratamento). Contraindicações: Gravidez e lactação, infecções ativas, doenças autoimunes, alergia a substâncias, doenças neuromusculares, câncer ativo. Cancelamento: 4h de antecedência.",
            "active": True
        },
        {
            "name": "Harmonização Corporal",
            "category": "Corporal",
            "duration_min": 90,
            "price_fixed": None,
            "requires_consultation": True,
            "consultation_price": 200.00,
            "cancellation_hours": 4,
            "room_id": sala_01_id,
            "description": "Tratamento individual mediante a necessidade de cada paciente que pode ser (gordura localizada ou circulatória, flacidez, celulite). Melhora geral do contorno do corpo.",
            "contraindications": "Infecções ou inflamações na pele, Doenças cardíacas graves, Trombose ou problemas circulatórios ativos, câncer ativo ou recente, diabetes descompensada, Problemas renais ou hepáticos graves, Gravidez e lactação.",
            "post_treatment_care": "Beber de 2 a 3L de água por dia, manter alimentação saudável e praticar atividade física."
        },
        {
            "name": "Drenagem Linfática",
            "category": "Corporal",
            "duration_min": 60,
            "price_fixed": 200.00,
            "cancellation_hours": 24,
            "room_id": sala_01_id,
            "description": "A drenagem linfática é uma massagem suave que estimula o sistema linfático, ajudando a eliminar líquidos e toxinas do corpo. É usada para reduzir inchaços, melhorar a circulação, tratar celulite e auxiliar no pós-operatório.",
            "contraindications": "Infecções agudas, Trombose venosa profunda, Insuficiência cardíaca descompensada, Problemas renais graves e Câncer ativo (sem autorização médica).",
            "post_treatment_care": "Beber bastante água, manter uma alimentação leve e saudável."
        },
        {
            "name": "Massagem Modeladora",
            "category": "Corporal",
            "duration_min": 60,
            "price_fixed": 200.00,
            "cancellation_hours": 24,
            "room_id": sala_01_id,
            "description": "Massagem vigorosa para modelar o corpo e reduzir medidas.",
            "contraindications": "Gravidez, problemas circulatórios graves.",
            "post_treatment_care": "Hidratação adequada e alimentação balanceada."
        },
        {
            "name": "Diástase",
            "category": "Corporal",
            "duration_min": 60,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 4,
            "room_id": sala_01_id,
            "equipment_id": criofreq_id,
            "description": "Trata disfunção abdominal fechando a diástase em até 70% melhorando também o quadro de flacidez e gordura localizada caso a cliente venha ter. Além de outras questões como dores nas costas, melhora da postura, causadas devido a disfunção.",
            "contraindications": "Hipertensos e pacientes com câncer.",
            "post_treatment_care": "Evitar carboidratos em excesso, açúcares em geral, ingerir 2 a 3L de água por dia e praticar atividade física com frequência."
        },
        {
            "name": "Criolipólise de Placas",
            "category": "Corporal",
            "duration_min": 480,  # 8 hours
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 24,
            "room_id": sala_04_id,
            "equipment_id": criolipo_id,
            "description": "Tratamento estético não invasivo destinado à redução de gordura localizada por meio do resfriamento controlado, realizado por placas que são colocadas diretamente sobre a pele.",
            "contraindications": "Gestantes, hérnias na região a ser tratada, feridas, infecções, doenças hepáticas graves, distúrbios circulatórios graves, diabetes descompensado.",
            "post_treatment_care": "Beber de 2 a 3L de água, manter uma alimentação saudável, praticar atividade física, fazer o uso da cinta e drenagem linfática manual."
        },
        {
            "name": "Microfocado",
            "category": "Facial",
            "duration_min": 120,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 4,
            "room_id": sala_01_id,
            "description": "O ultrassom microfocado é uma técnica estética avançada que utiliza energia de ultrassom focalizada para tratar a flacidez da pele e promover o rejuvenescimento facial, estimulando a produção de colágeno e elastina.",
            "contraindications": "Gravidez e lactação, doenças de pele ativas, implantes metálicos ou marcapasso, pele sensível ou tendência a queloides, distúrbios de coagulação e histórico de câncer de pele.",
            "post_treatment_care": "Seguir orientações específicas do profissional."
        },
        {
            "name": "Pein (Varizes)",
            "category": "Corporal",
            "duration_min": 60,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 24,
            "room_id": sala_01_id,
            "description": "É um tratamento estético que visa melhorar a aparência das varizes e vasos sanguíneos visíveis na pele.",
            "contraindications": "Não deve ser aplicado em áreas com infecções, feridas abertas, gravidez e lactação, doenças de pele grave, históricos de reações alérgicas, problemas circulatórios graves.",
            "post_treatment_care": "Seguir orientações do profissional."
        },
        {
            "name": "Apartamento Pós-Operatório",
            "category": "Pós-Operatório",
            "duration_min": 7200,  # 5 days
            "price_fixed": 4000.00,
            "cancellation_hours": 48,
            "room_id": apartamento_id,
            "description": "Cama confortável com enxoval limpo, ambientes climatizados e silenciosos, acessibilidade (sem escadas), Wi-Fi, TV, cadeira de apoio p/ pós operatório, serviço de limpeza, 4 refeições ao dia e uma pessoa a disposição.",
            "contraindications": None,
            "post_treatment_care": "Seguir orientações médicas pós-cirúrgicas."
        },
        {
            "name": "Laser Lavieen",
            "category": "Facial",
            "duration_min": 40,
            "price_fixed": None,
            "requires_consultation": True,
            "consultation_price": 0.00,  # Free evaluation
            "cancellation_hours": 4,
            "room_id": sala_01_id,
            "description": "Opção para rejuvenescimento, tratamento de manchas, flacidez e sinais de envelhecimento. Sua ação fracionada e não invasiva garante alta eficácia com mínima recuperação.",
            "contraindications": "Gravidez, lactação, infecções ativas, câncer de pele.",
            "post_treatment_care": "Proteção solar rigorosa, hidratação."
        },
        {
            "name": "Lipo de Papada",
            "category": "Facial",
            "duration_min": 120,
            "price_fixed": 4500.00,
            "cancellation_hours": 48,
            "room_id": sala_01_id,
            "description": "Procedimento estético que visa a remoção de gordura localizada na região submentoniana (abaixo do queixo), melhorando o contorno do pescoço e da linha da mandíbula.",
            "contraindications": "Gravidez, lactação, infecções, problemas de coagulação.",
            "post_treatment_care": "Uso de cinta, drenagem linfática, repouso."
        },
        {
            "name": "Endolaser",
            "category": "Corporal",
            "duration_min": 120,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 48,
            "room_id": sala_01_id,
            "description": "Tratamento minimamente invasivo que trabalha na camada subcutânea da pele reduzindo gordura localizada e flacidez e pode ser feito em várias áreas do corpo.",
            "contraindications": "Gravidez, lactação, infecções, problemas circulatórios graves.",
            "post_treatment_care": "Repouso, uso de cinta, drenagem linfática."
        },
        {
            "name": "Camuflagem de Cicatriz e Estrias",
            "category": "Corporal",
            "duration_min": 90,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 24,
            "room_id": sala_01_id,
            "description": "Tratamento estético que visa disfarçar marcas e imperfeições na pele, como cicatrizes pós-cirúrgicas, de acne, ou estrias, proporcionando um efeito visual de uniformização.",
            "contraindications": "Infecções de pele, gravidez e lactação, histórico de queloides, distúrbios de coagulação, uso de medicamentos fotossensibilizantes, pele irritada, alergia a pigmentos e doenças autoimunes.",
            "post_treatment_care": "Proteção solar, hidratação, evitar exposição ao sol."
        },
        {
            "name": "Reconstrução de Aréola",
            "category": "Corporal",
            "duration_min": 60,
            "price_fixed": None,
            "requires_consultation": True,
            "cancellation_hours": 24,
            "room_id": sala_01_id,
            "description": "Procedimento estético que visa restaurar a aparência das aréolas e mamilos, especialmente após cirurgias como a mastectomia, lesões ou deformidades congênitas.",
            "contraindications": "Infecções ativas na área da mama, doenças autoimunes, alergia a pigmentos, gravidez e lactação, imunossupressão, pele danificada ou enfraquecida.",
            "post_treatment_care": "Cuidados específicos com a área, proteção solar."
        },
    ]
    
    print("\nSeeding services...")
    for service in services:
        result = supabase.table("services").upsert(service, on_conflict="name").execute()
        print(f"  ✓ {service['name']}")
    
    print(f"\nTotal services seeded: {len(services)}")


async def seed_message_templates():
    """Insert message templates"""
    supabase = supabase_client.client
    
    templates = [
        {
            "name": "POS_VENDA_TRATAMENTO_CORPORAL",
            "content": "OLÁ! NOSSO TRATAMENTO FINALIZOU, GOSTARIA DE SABER O QUE VOCÊ ACHOU DO NOSSO ATENDIMENTO E SE GOSTOU DO SEU RESULTADO. SEU FEEDBACK É MUITO IMPORTANTE. 💛",
            "category": "feedback",
            "variables": []
        },
        {
            "name": "REGRAS_AGENDAMENTO_LASER",
            "content": """Nosso combinado para o melhor atendimento:
• Podemos esperar até 10 minutos de atraso.
• Se precisar cancelar, nos avise com pelo menos um dia de antecedência.
• Quando não houver aviso e o paciente não comparecer, a sessão será registrada como feita.

Obrigada por valorizar o nosso tempo — assim conseguimos atender a todos com qualidade 💛""",
            "category": "policy",
            "variables": []
        },
        {
            "name": "AGENDAMENTO_HIPERBARICA",
            "content": "CLIENTES QUE IRÃO FAZER HIPERBÁRICA, PEDIMOS QUE ORGANIZEM SEUS HORÁRIOS E NOS PASSEM COM ANTECEDÊNCIA. ISSO É PARA EVITAR TRANSTORNOS COM O NOSSO AGENDAMENTO AQUI NA CLÍNICA.",
            "category": "policy",
            "variables": []
        },
        {
            "name": "TAXA_BANHO_POS_OP",
            "content": "PACIENTES QUE TÊM ACOMPANHANTE, MAS NECESSITAM DO BANHO NA CLÍNICA, É COBRADO UMA TAXA DE R$500,00 PARA O BANHO NAS SESSÕES.",
            "category": "pricing",
            "variables": []
        },
        {
            "name": "CONSULTA_HARMONIZACAO",
            "content": """Olá paciente querida 🥰, a nossa consulta para harmonização hoje é personalizada, onde você passa por um exame imediato, que identifica vários parâmetros negativos do seu organismo. Assim sendo passadas prescrições e recomendações para corrigir e ajudar a melhorar o seu organismo, mesmo que a paciente não faça procedimento conosco. O valor da nossa consulta R$200.00. Esse valor pode ser abatido no tratamento, caso a paciente venha a adquirir. PARA AGENDAMENTO É NECESSÁRIO 30% DO VALOR E O RESTANTE NO ATO.""",
            "category": "consultation",
            "variables": []
        },
        {
            "name": "POS_OPERATORIO_CORPORAL",
            "content": """Olá tudo bem? Você sabia que temos um acompanhamento P. O profissional e avançado, com técnicas modernas para cada tipo de cirurgia plástica? Nosso acompanhamento pode ir desde os primeiros dias com drenos até um pós operatório tardio onde chegamos na etapa de evolução cicatricial final e definição da estrutura corporal. Abaixo temos opções de quantidades de sessões. Independente de associações ou não o valor será o mesmo.
• 05 sessões de pós operatório • R$ 1.500,00 • ou 10x de R$ 164,80
• 10 sessões de pós operatório • R$ 2.500,00 • ou 10x de R$ 274,67 💳
• 20 sessões de pós operatório • R$ 3.500,00 • ou 10x de R$ 384,53""",
            "category": "pricing",
            "variables": []
        },
        {
            "name": "CONSULTA_MOUNJARO",
            "content": """CONSULTA: 280,00. ESSE VALOR PODE SER ISENTO CASO O PACIENTE FECHE O TRATAMENTO NO ATO DA CONSULTA OU EM ATÉ 24HS. INCLUSO: AVALIAÇÃO E MAPEAMENTO FISIOLÓGICOS, ORIENTAÇÃO NUTRICIONAL, PRESCRIÇÃO PARA SUPLEMENTAÇÃO, EXAME DE BIORRESSONÂNCIA E BIOIMPEDÂNCIA, AVALIAÇÃO DE COMPOSIÇÃO CORPORAL, INDICAÇÃO DE TRATAMENTO. Para o agendamento é necessário 50% do valor e o restante no ato da consulta.""",
            "category": "consultation",
            "variables": []
        },
        {
            "name": "CONSULTA_BIOMEDICA",
            "content": """O valor de nossa consulta fica R$150,00 e esse valor pode ser abatido em qualquer tratamento que a paciente venha adquirir COM A DR LOURRANY. Para o agendamento é necessário 50% do valor e o restante no ato da consulta. Posso estar agendando!?""",
            "category": "consultation",
            "variables": []
        },
        {
            "name": "LASER_LAVIEEN",
            "content": """Olá! Sobre o tratamento laser lavieen, nosso BB glow avançado, ele é indicado para várias queixas faciais e corporais, como, melasma, rejuvenescimento, cicatrizes de acne, e até clareamento de áreas como virilha e axilas, e manchas corporais. Valores e indicações de tratamento somente mediante consulta. AVALIAÇÃO PARA O LASER LAVIEEN GRATUITA!""",
            "category": "treatment_info",
            "variables": []
        },
        {
            "name": "TIRZEPATIDA",
            "content": """TIRZEPATIDA é uma aplicação com uma injeção insulínica que provoca a sensação de saciedade. Antes da realização desse procedimento é necessário realizarmos uma consulta para que a Dra possa avaliar. VALORES E INDICAÇÃO DA QUANTIDADE DE SESSÕES (CANETAS), DEPENDEM DO BIOTIPO E DAS INDIVIDUALIDADES DE CADA UM. POR ISSO A CONSULTA É DE SUMA IMPORTÂNCIA.""",
            "category": "treatment_info",
            "variables": []
        },
        {
            "name": "LIPO_PAPADA_PROMOCAO",
            "content": """LANÇAMENTO DA LIPO DE PAPADA AVANÇADA COM ALTA DEFINIÇÃO DE R$5.500 POR R$4.500 EM ATÉ 10X SEM JUROS NOS CARTÕES. CONDIÇÕES COM PÓS: LIPO DE PAPADA + 10 SESSÕES DE DRENAGEM PÓS OPERATÓRIO R$5.500 EM ATÉ 10X SEM JUROS.""",
            "category": "promotion",
            "variables": []
        },
        {
            "name": "ATENDIMENTO_DOMICILIO",
            "content": """Infelizmente não fazemos atendimento a domicílio, não se preocupe, a clínica é preparada para receber você, com macas e materiais próprios. E as suas vindas aqui vão lhe fazer bem.""",
            "category": "policy",
            "variables": []
        },
        {
            "name": "CUIDADOS_POS_CIRURGIAS_FACIAIS",
            "content": """Retirada, limpeza e troca de curativo, ledterpia para cicatrização, terapias manuais e acompanhamento.
• 1 sessão: R$250 a vista
• 2 sessões: R$400,00 a vista
• 5 sessões: R$800,00 a vista (somente para nariz e blefaroplastia)
• 10 sessões: R$1.200 a vista (somente para lipo de papada)
• 10 sessões: R$1.800 para cirurgia dupla ou tripla quando inclui o lifting facial.
PARA PARCELAMENTO CONSULTAR TAXA.""",
            "category": "pricing",
            "variables": []
        },
    ]
    
    print("\nSeeding message templates...")
    for template in templates:
        result = supabase.table("message_templates").upsert(template, on_conflict="name").execute()
        print(f"  ✓ {template['name']}")
    
    print(f"\nTotal templates seeded: {len(templates)}")


async def seed_knowledge_base():
    """Insert knowledge base articles"""
    supabase = supabase_client.client
    
    kb_articles = [
        {
            "title": "Informações Gerais da Clínica",
            "content": """Luana Carla Dermo Clinic
Endereço: Rua José Pereira Costa, 540, Centro, Canaã dos Carajás, PA, 68350-065
Telefone: (94) 99139-8585
Email: luanacarla.smendes@gmail.com

Horários de Funcionamento:
- Segunda a Sexta: 08:30 - 19:00
- Sábado: 08:30 - 12:00
- Domingo: Fechado

Política de Antecedência: Agendamentos devem ser feitos com no mínimo 1 hora de antecedência.
Intervalo entre procedimentos: 10 minutos.""",
            "category": "general",
            "keywords": ["horário", "endereço", "telefone", "contato", "funcionamento", "localização"],
            "version": "1.0"
        },
        {
            "title": "Política de Cancelamento",
            "content": """Políticas de Cancelamento por Tipo de Tratamento:

Harmonização Facial/Corporal:
- Cancelamento deve ser feito com até 4 horas de antecedência
- Cancelamentos fora do prazo: sessão será registrada como feita

Depilação a Laser:
- Cancelamento deve ser feito com até 24 horas de antecedência
- Cancelamentos fora do prazo: sessão será registrada como feita

Política de Reagendamento:
- Permitido até 2 reagendamentos
- Aviso prévio de 4 horas necessário

Política de No-Show:
- Em caso de não comparecimento sem aviso, o cliente perde o direito ao reagendamento
- A sessão será dada como feita""",
            "category": "policy",
            "keywords": ["cancelamento", "reagendamento", "no-show", "falta", "política", "aviso"],
            "version": "1.0"
        },
        {
            "title": "Depilação a Laser - Informações Completas",
            "content": """Depilação a Laser

Descrição: Método de remoção dos pelos que utiliza feixes de luz concentrada (laser) para destruir os folículos pilosos. Técnica eficaz e duradoura que reduz significativamente o crescimento dos pelos ao longo do tempo.

Equipamento: Laser Galaxy Fiber
Sala: Sala 02
Duração: 60 minutos

Contraindicações:
- Gravidez
- Doenças de pele
- Câncer de pele
- Pele muito bronzeada ou com queimaduras solares
- Diabetes

Cuidados Pós-Tratamento:
- Evitar exposição ao sol por pelo menos 7 dias
- Usar protetor solar com FPS 30 ou mais
- Hidratar a pele regularmente
- Não usar produtos irritantes
- Bronzeamento permitido apenas após 15 dias

Política de Cancelamento: 24 horas de antecedência""",
            "category": "treatment",
            "keywords": ["depilação", "laser", "pelos", "galaxy fiber", "bronzeamento", "sol"],
            "version": "1.0"
        },
        {
            "title": "Harmonização Facial - Informações Completas",
            "content": """Harmonização Facial

Descrição: Procedimentos incluem Ácido Hialurônico, Botox, Lift de Fios, Bioestimuladores de Colágeno.

Duração: 60 minutos
Sala: Sala 03 (Consulta)
Requer Consulta: Sim
Valor da Consulta: R$ 200,00 (pode ser abatido no tratamento)

Indicações:
- Rejuvenescer e suavizar rugas
- Melhorar a simetria e contorno do rosto
- Aumentar o volume e definir áreas
- Tratar flacidez e estimular colágeno

Contraindicações:
- Gravidez e lactação
- Infecções ativas
- Doenças autoimunes
- Alergia a substâncias
- Doenças neuromusculares
- Câncer ativo ou em tratamento

Política de Cancelamento: 4 horas de antecedência

Agendamento: Necessário 30% do valor da consulta para agendar, restante no ato.""",
            "category": "treatment",
            "keywords": ["harmonização", "facial", "botox", "ácido hialurônico", "rugas", "rejuvenescimento"],
            "version": "1.0"
        },
        {
            "title": "Drenagem Linfática - Informações Completas",
            "content": """Drenagem Linfática

Descrição: Massagem suave que estimula o sistema linfático, ajudando a eliminar líquidos e toxinas do corpo.

Duração: 60 minutos
Preço: R$ 200,00
Sala: Sala 01

Indicações:
- Retenção de líquidos
- Inchaço e edema
- Pós-operatório
- Celulite
- Linfedema
- Má circulação
- Gravidez (a partir dos 3 meses)

Contraindicações:
- Infecções agudas
- Trombose venosa profunda
- Insuficiência cardíaca descompensada
- Problemas renais graves
- Câncer ativo (sem autorização médica)

Cuidados Pós-Tratamento:
- Beber bastante água
- Manter alimentação leve e saudável

Política de Cancelamento: 24 horas de antecedência""",
            "category": "treatment",
            "keywords": ["drenagem", "linfática", "inchaço", "edema", "pós-operatório", "retenção"],
            "version": "1.0"
        },
        {
            "title": "Apartamento Pós-Operatório",
            "content": """Apartamento para Pós-Operatório

Preço: R$ 4.000,00 por 5 dias

Incluso na Estadia:
- Cama confortável com enxoval limpo
- Ambientes climatizados e silenciosos
- Acessibilidade (sem escadas)
- Wi-Fi e TV
- Cadeira de apoio para pós-operatório
- Serviço de limpeza
- 4 refeições por dia
- Uma pessoa à disposição
- Sessões de terapia pós-operatório manual
- Ozonioterapia (se necessário)
- Retirada do dreno com 3 dias

Observações Importantes:
- É necessário que a paciente tenha acompanhante
- Caso não tenha, solicitar valor do acompanhamento pela clínica
- Pacientes com acompanhante que necessitam banho na clínica: taxa de R$ 500,00

Horário de Atendimento no Fim de Semana: 8h às 19h

Política de Cancelamento: 48 horas de antecedência""",
            "category": "treatment",
            "keywords": ["apartamento", "pós-operatório", "estadia", "recuperação", "dreno", "acompanhamento"],
            "version": "1.0"
        },
        {
            "title": "Tratamento Mounjaro (Tirzepatida)",
            "content": """Tratamento Mounjaro - Planos Redesign

Descrição: Tratamento focado na perda de peso e redesenho corporal utilizando Tirzepatida (Mounjaro), combinado com acompanhamento e terapias de suporte.

Consulta Necessária: Sim
Valor da Consulta: R$ 280,00
Isenção: Valor pode ser isento se fechar tratamento no ato ou em até 24h
Agendamento: Necessário 50% do valor da consulta

Plano 1 - Redesign Start:
Preço: R$ 1.700,00 ou 6x de R$ 316,00
Incluso:
- 4 doses de Tirzepatida (Mounjaro) 2,5mg
- 1 aplicação Imunitbooster
- 1 detox injetável
- Bioimpedância
- Acompanhamento semanal
- Orientação e Plano alimentar
- Acompanhamento por 30 dias

Plano 2 - Redesign Power:
Preço: R$ 3.499,00 ou 10x de R$ 370,00
Incluso:
- Acompanhamento por 30 dias
- Analisador fisiológico (biorressonância)
- Bioimpedância
- 4 doses de Tirzepatida (Mounjaro) 2,5mg
- 4 sessões Detox Power
- 1 detox injetável
- 1 kit detox (manipulados para 15 dias)
- 1 aplicação do Imunitbooster
- Acompanhamento semanal
- Orientação e plano alimentar

Observação: Valores e indicação de quantidade de sessões dependem do biotipo e individualidades de cada paciente.""",
            "category": "treatment",
            "keywords": ["mounjaro", "tirzepatida", "emagrecimento", "perda de peso", "redesign"],
            "version": "1.0"
        },
        {
            "title": "Laser Lavieen",
            "content": """Laser Lavieen - BB Glow Avançado

Descrição: Opção para rejuvenescimento, tratamento de manchas, flacidez e sinais de envelhecimento. Ação fracionada e não invasiva com alta eficácia e mínima recuperação.

Duração: 30 a 40 minutos
Avaliação: GRATUITA
Valores: Mediante consulta

Indicações:
- Envelhecimento facial
- Flacidez
- Manchas e hiperpigmentação
- Cicatrizes de acne
- Poros dilatados
- Melhora geral na textura da pele
- Melasma
- Clareamento de áreas (virilha, axilas)
- Manchas corporais

Contraindicações:
- Gravidez
- Lactação
- Infecções ativas
- Câncer de pele

Cuidados Pós-Tratamento:
- Proteção solar rigorosa
- Hidratação adequada""",
            "category": "treatment",
            "keywords": ["laser", "lavieen", "bb glow", "manchas", "melasma", "rejuvenescimento"],
            "version": "1.0"
        },
        {
            "title": "Lipo de Papada",
            "content": """Lipo de Papada Avançada com Alta Definição

Descrição: Procedimento estético que visa a remoção de gordura localizada na região submentoniana (abaixo do queixo), melhorando o contorno do pescoço e da linha da mandíbula.

Duração: 2 horas
Preço Promocional: R$ 4.500,00 (de R$ 5.500,00)
Parcelamento: Até 10x sem juros nos cartões

Pacote com Pós-Operatório:
- Lipo de Papada + 10 sessões de drenagem pós-operatório
- Preço: R$ 5.500,00 em até 10x sem juros

Contraindicações:
- Gravidez
- Lactação
- Infecções
- Problemas de coagulação

Cuidados Pós-Tratamento:
- Uso de cinta
- Drenagem linfática
- Repouso adequado

Política de Cancelamento: 48 horas de antecedência""",
            "category": "treatment",
            "keywords": ["lipo", "papada", "queixo", "pescoço", "gordura localizada"],
            "version": "1.0"
        },
        {
            "title": "Locação de Poltronas para Pós-Operatório",
            "content": """Locação de Poltronas para Pós-Operatório

Descrição: Investir em uma poltrona reclinável para o seu período pós-operatório é uma escolha de conforto e cuidado com sua saúde e bem-estar.

Benefícios:
- Posicionamento Ajustável: Reduz pressão sobre áreas sensíveis
- Suporte Ergonômico: Alivia tensão muscular e promove postura correta
- Facilidade de Movimentação: Levanta suavemente sem esforço
- Conforto Contínuo: Estofamento macio e apoio para os pés
- Sono adequado: Melhor qualidade de sono para recuperação

Tabela de Preços:
- 1 dia: R$ 150,00
- 5 dias: R$ 625,00
- 10 dias: R$ 1.100,00
- 15 dias: R$ 1.500,00

Taxa de Frete:
- R$ 100,00 para buscar e deixar em Canaã dos Carajás
- Para Parauapebas e cidades próximas: consultar frete com endereço""",
            "category": "service",
            "keywords": ["poltrona", "locação", "pós-operatório", "recuperação", "conforto"],
            "version": "1.0"
        },
        {
            "title": "Pacotes de Pós-Operatório Corporal",
            "content": """Pós-Operatório Corporal - Pacotes de Sessões

Descrição: Acompanhamento profissional e avançado com técnicas modernas para cada tipo de cirurgia plástica. Desde os primeiros dias com drenos até a etapa de evolução cicatricial final e definição da estrutura corporal.

Pacotes Disponíveis:
- 5 sessões: R$ 1.500,00 ou 10x de R$ 164,80
- 10 sessões: R$ 2.500,00 ou 10x de R$ 274,67
- 20 sessões: R$ 3.500,00 ou 10x de R$ 384,53

Observação: Independente de associações ou não, o valor será o mesmo.

O que está incluído:
- Drenagem linfática manual
- Terapias manuais específicas
- Acompanhamento da evolução
- Técnicas modernas para cada tipo de cirurgia""",
            "category": "service",
            "keywords": ["pós-operatório", "sessões", "drenagem", "cirurgia plástica", "pacote"],
            "version": "1.0"
        },
        {
            "title": "Cuidados Pós-Operatórios de Cirurgias Faciais",
            "content": """Cuidados Pós-Operatórios de Cirurgias Faciais

Serviços Inclusos:
- Retirada, limpeza e troca de curativo
- Ledterapia para cicatrização
- Terapias manuais
- Acompanhamento profissional

Tabela de Preços:
- 1 sessão: R$ 250,00 à vista
- 2 sessões: R$ 400,00 à vista
- 5 sessões: R$ 800,00 à vista (somente para nariz e blefaroplastia)
- 10 sessões: R$ 1.200,00 à vista (somente para lipo de papada)
- 10 sessões: R$ 1.800,00 (cirurgia dupla ou tripla com lifting facial)

Observação: Para parcelamento, consultar taxa.""",
            "category": "service",
            "keywords": ["pós-operatório", "facial", "nariz", "blefaroplastia", "lifting", "curativo"],
            "version": "1.0"
        },
        {
            "title": "Consultas - Tipos e Valores",
            "content": """Consultas Disponíveis na Clínica

1. Consulta para Harmonização (Luana):
   - Valor: R$ 200,00
   - Incluso: Exame imediato que identifica parâmetros do organismo
   - Prescrições e recomendações personalizadas
   - Valor pode ser abatido no tratamento
   - Agendamento: 30% do valor + restante no ato

2. Consulta Mounjaro:
   - Valor: R$ 280,00
   - Pode ser isento se fechar tratamento no ato ou em até 24h
   - Incluso: Avaliação e mapeamento fisiológicos, orientação nutricional, prescrição para suplementação, exame de biorressonância e bioimpedância
   - Agendamento: 50% do valor + restante no ato

3. Consulta Biomédica (Dra. Lourrany):
   - Valor: R$ 150,00
   - Valor pode ser abatido em qualquer tratamento com a Dra. Lourrany
   - Agendamento: 50% do valor + restante no ato

4. Avaliação Laser Lavieen:
   - GRATUITA""",
            "category": "service",
            "keywords": ["consulta", "avaliação", "harmonização", "mounjaro", "biomédica", "preço"],
            "version": "1.0"
        },
    ]
    
    print("\nSeeding knowledge base...")
    for article in kb_articles:
        result = supabase.table("knowledge_base").upsert(article, on_conflict="title").execute()
        print(f"  ✓ {article['title']}")
    
    print(f"\nTotal KB articles seeded: {len(kb_articles)}")


async def main():
    """Main seed function"""
    print("=" * 60)
    print("CLÍNICA LUANA - DATABASE SEED SCRIPT")
    print("=" * 60)
    
    try:
        # Seed rooms first
        rooms_data = await seed_rooms()
        rooms_map = {room["name"]: room["id"] for room in rooms_data}
        
        # Seed equipment
        equipment_data = await seed_equipment(rooms_map)
        equipment_map = {equip["name"]: equip["id"] for equip in equipment_data}
        
        # Seed services
        await seed_services(rooms_map, equipment_map)
        
        # Seed message templates
        await seed_message_templates()
        
        # Seed knowledge base
        await seed_knowledge_base()
        
        print("\n" + "=" * 60)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • {len(rooms_data)} rooms")
        print(f"  • {len(equipment_data)} equipment items")
        print(f"  • Services seeded (check output above)")
        print(f"  • Message templates seeded (check output above)")
        print(f"  • Knowledge base articles seeded (check output above)")
        print("\nNext steps:")
        print("  1. Verify data in Supabase dashboard")
        print("  2. Test FAQ agent with knowledge base queries")
        print("  3. Test scheduler agent with service availability")
        
    except Exception as e:
        print(f"\n❌ ERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
