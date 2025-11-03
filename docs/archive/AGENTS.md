# Repository Guidelines

## Project Structure & Module Organization
- `app/` runs the FastAPI gateway; `main.py` is the local entrypoint.
- Agents live in `agents/` with shared helpers in `tools/`, `services/`, `models/`, and `utils/`; clients and configuration stay in `config/`, and background tasks sit in `jobs/` and `scripts/`.
- Documentation and assets stay in `docs/`, `examples/`, and `static/`, while `tests/` mirrors runtime modules for fast lookup.

## Build, Test, and Development Commands
Create a Python 3.13 virtual environment, then:
```
pip install -r requirements.txt
uvicorn main:app --reload
```
- `pytest`: run the async-aware unit and integration suite.
- `pytest --cov=app tests`: confirm coverage expectations before merging.
- `python tests/run_integration_tests.py`: exercise Chatwoot, Redis, and Supabase flows without production dependencies.
- `black .`, `flake8 .`, `mypy app tests`: apply formatting, linting, and typing checks that gate CI.

## Coding Style & Naming Conventions
- Format with Black (line length 88) and four-space indentation; rely on Black for import ordering.
- Use `snake_case` for functions and files, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants and environment variables.
- Keep type hints in place, reuse Pydantic models from `models/`, and name agent files after their role (for example `faq_agent.py` defines `FaqAgent`).

## Testing Guidelines
- Add tests near their targets using the `test_<module>.py` convention and extend end-to-end flows in `tests/test_e2e.py`.
- Mock external IO with `responses` or in-repo fixtures; CI must not hit live services.
- Record manual checks in `tests/E2E_TEST_GUIDE.md`, block merges until `pytest --cov` passes, and update `tests/test_tools.py` plus cache suites when agent tooling changes.

## Commit & Pull Request Guidelines
- Follow the existing history: capitalized, present-tense subject lines that name the subsystem (for example `Update FAQ agent module`).
- Keep commits focused; configuration or secret template changes (`.env`, `config/`) should stand alone for rollback clarity.
- Pull requests need an impact summary, validation commands, relevant ticket links, and screenshots or logs for UX-facing changes; request an agent maintainer review whenever `agents/` or `tools/` is touched.

## Environment & Secrets
- Copy `.env.example` to `.env`, supply Supabase, Redis, Chatwoot, and LLM credentials, then run `python scripts/validate_env.py`.
- Before Railway deploys through `start.sh`, run `python scripts/verify_deployment.py` to confirm platform parity.
- Never commit secrets; use Railway environment variables and Supabase secret storage in shared environments.
