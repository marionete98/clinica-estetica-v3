"""
Script para reorganizar documentação - mover arquivos .md da raiz para docs/archive/
"""
import shutil
from pathlib import Path

# Arquivos na raiz que devem ser movidos para archive
root_md_files = [
    "AGENTS.md",
    "ANALISE_RISCO_JSON.md",
    "APRESENTACAO_REVIEW.md",
    "AUTOGEN_DEPENDENCY_FIX_SUMMARY.md",
    "BUGFIX_SUMMARY.md",
    "CHANGELOG_AUTOGEN_REVIEW.md",
    "CHATWOOT_IMPROVEMENTS_QUICKSTART.md",
    "CORREÇÕES_APLICADAS.md",
    "DEPLOYMENT_QUICK_REFERENCE.md",
    "DOCUMENTO DE COLETA DE DADOS ESSENCIAIS – CLÍNICA LUANA(completo).md",
    "EXECUTIVE_SUMMARY_AUTOGEN_REVIEW.md",
    "GEMINI.md",
    "IMPLEMENTATION_CHECKLIST.md",
    "MIGRATIONS_APPLIED.md",
    "PRODUCTION_DEPLOYMENT_FIX.md",
    "PRODUCTION_READINESS_REVIEW.md",
    "PRODUCTION_RUNTIME_FIXES.md",
    "PRODUCTION_VALIDATION_QUICKSTART.md",
    "RAILWAY_ENV_VARIABLES.md",
    "REDIS_CACHE_QUICKSTART.md",
    "RELATORIO_FINAL_PRODUCAO.md",
    "REVIEW_SUMMARY_VISUAL.md",
]

root_dir = Path(__file__).parent
archive_dir = root_dir / "docs" / "archive"

# Garantir que o diretório archive existe
archive_dir.mkdir(parents=True, exist_ok=True)

moved_count = 0
skipped_count = 0

print("=" * 60)
print("REORGANIZANDO DOCUMENTAÇÃO")
print("=" * 60)

for filename in root_md_files:
    source = root_dir / filename
    destination = archive_dir / filename
    
    if source.exists():
        try:
            shutil.move(str(source), str(destination))
            print(f"✅ Movido: {filename}")
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
