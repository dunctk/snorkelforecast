# Repository Guidelines

## Project Structure & Module Organization
- Django project in `snorkelforecast/` with settings at `snorkelforecast/snorkelforecast/settings.py` and entrypoint `snorkelforecast/manage.py`.
- Main app: `conditions/` (views, urls, templates).
- Static assets in `static/` (root, Tailwind output) and `snorkelforecast/static/` (project-scoped assets).
- Node/Tailwind config: `tailwind.config.mjs`, `package.json`. Python config: `pyproject.toml` (uses uv + ruff).

## Build, Test, and Development Commands
- Install deps (uv): `uv sync` (uses `pyproject.toml`/`uv.lock`).
- Run server: `uv run python snorkelforecast/manage.py runserver`.
- DB migrations: `uv run python snorkelforecast/manage.py makemigrations && uv run python snorkelforecast/manage.py migrate`.
- Tailwind (dev): `npm run tailwind:watch`.
- Tailwind (build): `npm run tailwind:build`.
- Lint: `uv run ruff check .`  |  Format: `uv run ruff format .`.
- Docker (prod-like): `docker build -t snorkelforecast . && docker run -p 8000:8000 snorkelforecast` (runs Gunicorn).

## Coding Style & Naming Conventions
- Python 3.12+, 4‑space indent, type hints encouraged.
- Keep Django app layout conventional: `views.py`, `urls.py`, `templates/<app>/`.
- Use snake_case for modules/functions, PascalCase for classes, kebab-case for static filenames when applicable.
- Run Ruff before PRs; keep diffs minimal and focused.

## Testing Guidelines
- Use Django’s test runner. Place tests in `conditions/tests/` (e.g., `test_views.py`).
- Name tests descriptively (`test_<functionality>_...`) and cover happy-path and edge cases.
- Run tests: `uv run python snorkelforecast/manage.py test`.

## Commit & Pull Request Guidelines
- Commit messages: prefix scope when helpful (e.g., `fix: ...`, `feat: ...`), imperative mood, concise subject, optional body.
- PRs should include: clear description, linked issue (if any), screenshots for UI changes, and a brief testing checklist.
- Keep PRs small and cohesive; avoid unrelated refactors.

## Git Hooks (Pre-commit)
- Install tooling: `uv add --dev pre-commit` then `uv run pre-commit install` and `uv run pre-commit install --hook-type pre-push`.
- Hooks run Ruff lint/format, basic checks, Conventional Commit message lint, and run Django tests on pre-push.
- Run locally: `uv run pre-commit run --all-files`.

## Security & Configuration Tips
- For production, set `DEBUG=false`, configure `ALLOWED_HOSTS`, and provide a secure `SECRET_KEY` via environment.
- Static files are served by WhiteNoise; run `collectstatic` in builds.
- Avoid committing secrets; use `.env.example` as a reference and load env vars in your runtime (container/orchestrator).
