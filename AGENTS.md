# Repository Guidelines

This guide orients new contributors to the multi-agent FastAPI stack that powers the clinic operations platform. Use it as a quick checklist before shipping code or reviews.

## Project Structure & Module Organization
- `main.py` exposes the FastAPI entrypoint and wires AutoGen agents; register startup hooks here to preserve health check behavior.
- `agents/` holds supervisor, intake, FAQ, scheduler, escalation, and follow-up personas; mirror `agents/README.md` when introducing new skills or tools.
- Shared infrastructure lives in `services/`, `middleware/`, and `jobs/`; extend these modules before creating ad-hoc helpers to keep orchestration predictable.
- HTTP surfaces reside in `routes/`, runtime knobs in `config/`, and deployment assets span `supabase/`, `docs/`, `scripts/`, and `static/`.
- Tests, fixtures, and mocks stay in `tests/`; update accompanying guides such as `tests/E2E_TEST_GUIDE.md` when workflows shift.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate`) provisions the Python 3.13 environment.
- `pip install -r requirements.txt` syncs pinned FastAPI 0.119, AutoGen 0.4, Semantic Kernel, and QA tooling.
- `uvicorn main:app --reload` boots the API and multi-agent orchestrator with auto-reload for local iteration.
- `pytest && pytest --cov=app tests` runs the async regression suite and validates the 85% coverage floor.
- `python scripts/validate_env.py` confirms XAI, Gemini, Supabase, and Redis credentials before Railway deployments.

## Coding Style & Naming Conventions
- Format touched files with `black` (line length 88) and `isort`; address `flake8` and `mypy` findings before raising a PR.
- Prefer snake_case for modules/functions, PascalCase for classes, and agent filenames that reflect their routing responsibility.
- Keep long prompts or transcripts in `docs/` or `static/prompts/`, and comment only when orchestration logic is non-obvious.

## Testing Guidelines
- Name tests `tests/test_<domain>_<scenario>.py` and mark async cases with `@pytest.mark.asyncio`; await Redis or Supabase helpers to avoid background leaks.
- Update `tests/test_scheduler_refactored.py` whenever `agents/scheduler.py` changes, and refresh co-located fixtures or mocks.
- Use targeted scripts (for example `python scripts/test_chatwoot_integration.py`) to validate integrations and capture outputs for reviews.

## Commit & Pull Request Guidelines
- Write imperative, capitalized commit subjects under 72 characters and list impacted subsystems (agents, services, routes, configs) in the body when relevant.
- Pull requests should document user impact, linked tickets, and proof of tests; attach latest `python scripts/validate_env.py` output for deployment-facing work.
- Request agent or DevOps reviewers when modifying `agents/`, `services/`, `jobs/`, or `supabase/`, and include Chatwoot/calendar evidence when required.

## Security & Configuration Tips
- Never hardcode secrets; rely on environment variables documented in `config/` and confirm via `scripts/validate_env.py`.
- Review `railway.json` and `docs/` runbooks before altering infra-facing settings, and flag any credential scope changes during reviews.

## Agent-Specific Instructions
- Align new personas with existing patterns in `agents/`; define capabilities in `agents/README.md` and register them in `main.py`.
- When extending orchestration flows, update relevant service or middleware modules first, then document operator-facing changes in `docs/`.
