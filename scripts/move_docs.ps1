$ErrorActionPreference = 'Stop'

$archive = Join-Path -Path 'docs' -ChildPath 'archive'
if (-not (Test-Path $archive)) {
    New-Item -ItemType Directory -Path $archive | Out-Null
}

$toMove = @(
    'docs\AGENTS_INDIVIDUAL_REVIEW.md',
    'docs\AGENTS_REVIEW_REPORT.md',
    'docs\AGENT_OPTIMIZATION_SUMMARY.md',
    'docs\AUTOGEN_BEST_PRACTICES_RECOMMENDATIONS.md',
    'docs\AUTOGEN_CODE_REVIEW_INDEX.md',
    'docs\AUTOGEN_REVIEW_ACTION_PLAN.md',
    'docs\AUTOGEN_REVIEW_CHECKLIST.md',
    'docs\AUTOGEN_REVIEW_DETAILED_FINDINGS.md',
    'docs\AUTOGEN_REVIEW_EXECUTIVE_SUMMARY.md',
    'docs\AUTOGEN_REVIEW_VISUAL_SUMMARY.md',
    'docs\AUTOGEN_SYSTEM_COMPREHENSIVE_REVIEW.md',
    'docs\CHATWOOT_COMPARISON_ANALYSIS.md',
    'docs\CHATWOOT_CONFIGURATION.md',
    'docs\CHATWOOT_DEPLOYMENT_GUIDE.md',
    'docs\CHATWOOT_IMPROVEMENTS_IMPLEMENTED.md',
    'docs\CHATWOOT_IMPROVEMENTS_TEST_GUIDE.md',
    'docs\CHATWOOT_INTEGRATION_CHECKLIST.md',
    'docs\CHATWOOT_TEST_SCRIPT_GUIDE.md',
    'docs\CODE_REVIEW_NOTES.md',
    'docs\COMPREHENSIVE_AUTOGEN_CODE_REVIEW.md',
    'docs\DEPLOYMENT_SUMMARY.md',
    'docs\ENV_ANALYSIS_REPORT.md',
    'docs\FAQ_CACHE_GUIDE.md',
    'docs\FAQ_CACHING_IMPLEMENTATION_SUMMARY.md',
    'docs\FAQ_REDIS_CACHE_INTEGRATION.md',
    'docs\FAQ_REDIS_INTEGRATION_SUMMARY.md',
    'docs\FOLLOWUP_AGENT_MIGRATION.md',
    'docs\GEMINI_SCHEDULER_INTEGRATION.md',
    'docs\IMPLEMENTATION_SUMMARY.md',
    'docs\IMPORTS_VERIFICATION_REPORT.md',
    'docs\KB_CACHE_FINAL_SUMMARY.md',
    'docs\KB_TOOLS_CACHED_DOCUMENTATION_UPDATE.md',
    'docs\LLM_STRATEGY_BY_AGENT_CORRECTED.md',
    'docs\LLM_STRATEGY_CORRECTION_SUMMARY.md',
    'docs\MANUAL_QA_CHECKLIST.md',
    'docs\MESSAGE_DEDUPLICATION_AND_BATCHING.md',
    'docs\OBSERVABILITY_IMPLEMENTATION.md',
    'docs\ORCHESTRATOR_ESCALATION_UPDATE.md',
    'docs\PRODUCTION_COMPATIBILITY_VALIDATION.md',
    'docs\PRODUCTION_RUNTIME_FIXES.md',
    'docs\RAILWAY_DEPLOYMENT_GUIDE.md',
    'docs\REDIS_KB_CACHE_IMPLEMENTATION.md',
    'docs\REDIS_MEMORY_VS_FAQ_CACHE.md',
    'docs\REQUIREMENTS_UPDATE_SUMMARY.md',
    'docs\REVIEW_INDEX.md',
    'docs\SCHEDULER_GEMINI_INTEGRATION.md',
    'docs\SUPERVISOR_PROMPT_ENHANCEMENT.md',
    'docs\TASK_14_DASHBOARD_IMPLEMENTATION.md',
    'docs\TASK_15_INTEGRATION_TESTS_SUMMARY.md',
    'docs\TASK_18_CHATWOOT_INTEGRATION_SUMMARY.md',
    'docs\TASK_18_VERIFICATION.md',
    'docs\TEST_E2E_IMPLEMENTATION.md',
    'docs\UNIT_TESTS_SUMMARY.md'
)

foreach ($file in $toMove) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $archive -Force
    }
}

$toDelete = @(
    'docs\AGENT_MEMORY_ARCHITECTURE.md',
    'docs\FLUXO_ATENDIMENTO_VISUAL.md'
)

foreach ($file in $toDelete) {
    if (Test-Path $file) {
        Remove-Item -Path $file -Force
    }
}
