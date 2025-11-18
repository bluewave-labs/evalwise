# Repository Guidelines

## Project Structure & Module Organization
- `api/`: FastAPI backend (Alembic migrations, Celery, tests under `api/tests`).
- `web/`: Next.js 15 + TypeScript frontend (TailwindCSS, ESLint).
- `scripts/`: Helper scripts for seeding and demos.
- `sample_dataset_templates/`: CSV templates for datasets.
- `docker-compose*.yml`: Local dev and service orchestration.
- `Makefile`: Common developer commands.

## Build, Test, and Development Commands
- Backend (Dockerized): `make dev` — start API, DB, Redis for local dev.
- Full demo: `make demo` — migrate, start, seed, quick API checks.
- DB migrations: `make migrate` — run Alembic upgrades.
- Seed data: `make seed` — insert demo evaluators/scenarios/datasets.
- Inspect: `make logs` (API logs), `make status` (container status).
- Stop/clean: `make clean` — down + prune volumes.
- Frontend: `cd web && npm run dev | build | start | lint`.
- Backend tests: `cd api && pytest -v` (use `-m unit|integration|auth|api`).

## Coding Style & Naming Conventions
- Python (api): 4-space indentation; PEP 8; modules `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- TypeScript/React (web): components export `PascalCase`; files in `web/src/components` use kebab-case (e.g., `scenario-preview-modal.tsx`).
- Imports: prefer relative within package boundaries; avoid circular deps.
- Formatting: use project defaults (ESLint for `web/` via `npm run lint`).

## Testing Guidelines
- Framework: Pytest (`api/pytest.ini` configured). Test files: `test_*.py`, classes `Test*`, functions `test_*`.
- Run: `cd api && pytest -v` or targeted (e.g., `pytest tests/test_auth.py -m auth`).
- Optional coverage: `pytest --cov=.` if `pytest-cov` is available.
- Add minimal, focused tests near the code under test; prefer unit over integration unless necessary.

## Commit & Pull Request Guidelines
- Commits: concise imperative subject (≤72 chars). Example: `feat(api): add PII regex evaluator`.
- Include rationale and scope in body; reference issues (`Closes #123`).
- PRs: clear description, steps to test, screenshots for UI changes, and linked issue(s). Keep changes scoped.

## Security & Configuration Tips
- Never commit secrets. Use `.env.example` to document new variables. Local envs: root `.env`, `api/.env`, `web/.env.local`.
- Default local URLs: API `http://localhost:8000`, Web `http://localhost:3000`.
