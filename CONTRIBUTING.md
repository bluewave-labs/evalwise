# Contributing

Thanks for your interest in improving EvalWise! This guide summarizes how to get set up, develop, and submit changes. For detailed project conventions, see `AGENTS.md`.

## Getting Started
- Prereqs: Docker + Docker Compose, Make, Node.js (for `web/`).
- Environment: copy `.env.example` to `.env` (and `api/.env`, `web/.env.local` as needed). Never commit secrets.

## Local Development
- Start services: `make dev` (API, Postgres, Redis) or `make demo` (migrate + seed + smoke checks).
- Useful targets: `make migrate`, `make seed`, `make logs`, `make status`, `make clean`.
- Frontend: `cd web && npm run dev` (and `npm run lint` before PRs).

## Testing
- Backend tests: `cd api && pytest -v`.
- Markers: `-m unit|integration|auth|api` (e.g., `pytest -m auth`).
- Optional coverage: `pytest --cov=.` if `pytest-cov` is available.

## Coding Standards
- Python: PEP 8, 4-space indentation, `snake_case` for files/functions/variables, `PascalCase` for classes.
- TypeScript/React: `PascalCase` components, kebab-case component filenames in `web/src/components`.
- See `AGENTS.md` for structure, naming, and additional tips.

## Commit & PR Process
- Branch: `feature/<short-name>`, `fix/<short-name>`, or `chore/<short-name>`.
- Commits: imperative and scoped. Example: `feat(api): add PII regex evaluator`.
- PRs should include:
  - Purpose and summary of changes
  - Testing notes (commands, expected outputs)
  - Screenshots for UI changes
  - Linked issue references (e.g., `Closes #123`)

## Resources
- Project guidelines: `AGENTS.md`
- Makefile commands: `make help`
- API docs (local): `http://localhost:8000/docs`
- Web app (local): `http://localhost:3000`
