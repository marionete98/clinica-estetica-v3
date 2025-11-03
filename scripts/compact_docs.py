"""
Script para compactar documentação - mover versões longas para archive
"""
import shutil
from pathlib import Path

# Arquivos em docs/ que devem ser movidos para archive (versões longas)
docs_to_archive = [
    "AGENTS_GUIDE.md",  # Temos AGENTS_GUIDE_COMPACT.md
    "CONFIGURATION_GUIDE.md",  # Temos CONFIGURATION_GUIDE_COMPACT.md
    "CALENDAR_API_ENDPOINTS.md",  # Duplicado de CALENDAR_API_DOCS.md
    "FAQ_CACHING_GUIDE.md",  # Detalhes técnicos, não essencial
    "PROMPT_LANGUAGE_OPTIMIZATION.md",  # Histórico de otimização
    "PRODUCTION_READINESS_REVIEW.md",  # Já temos TESTING_REPORT.md
]

docs_dir = Path("c:/exclusivo/clinica-estetica-v3/docs")
archive_dir = docs_dir / "archive"

moved_count = 0
skipped_count = 0

print("=" * 60)
print("COMPACTANDO DOCUMENTAÇÃO")
print("=" * 60)

for filename in docs_to_archive:
    source = docs_dir / filename
    destination = archive_dir / filename
    
    if source.exists():
        try:
            shutil.move(str(source), str(destination))
            print(f"✅ Movido para archive: {filename}")
            moved_count += 1
        except Exception as e:
            print(f"❌ Erro ao mover {filename}: {e}")
            skipped_count += 1
    else:
        print(f"⚠️  Não encontrado: {filename}")
        skipped_count += 1

print("\n" + "=" * 60)
print(f"RESULTADO: {moved_count} movidos, {skipped_count} pulados")
print("=" * 60)
