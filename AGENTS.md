# Repository Guidelines

## Project Structure & Modules
- `src/mvckivy/`: main package (app, base_mvc, uix, network, properties, translate, utils, project_management). KV assets live alongside their Python modules (e.g., `uix/buttons/icon_button.py` + `icon_button.kv`).
- `test/`: runnable UI demos and probes (e.g., `test/dialog_with_text_field_test/`), useful for manual verification.
- `main.py`: simple entry script for local smoke checks.
- `pyproject.toml`: Hatch/PEP 621 config with uv integration. Must be compatible with `uv` and `pip` commands.

## Build, Test, and Dev Commands
- Install (dev): `uv sync` — creates a virtual env and installs with `[dev]` group. `uv sync --upgrade` must be called before tests execution.
- Run a demo: `uv run python test/<demo>/main.py` (e.g., `test/lists_test/main.py`).
- Lint/format: `uv run black .` — autoformat; run before commits.
- Pytests (if added): `uv run pytest -q` — headless tests preferred.
- Build distribution: `uv build` (or `hatch build`) — produces wheel/sdist via hatchling.

## Coding Style & Naming
- Python 3.11, 4‑space indents, UTF‑8.
- Follow Black defaults; keep lines ≤ 88 chars.
- Naming: modules/files `snake_case.py`, classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_SNAKE_CASE`.
- KV files mirror Python names (e.g., `label.py` ↔ `label.kv`). Keep widget classes in `uix/*` and MVC bases in `base_mvc/*`.

## Testing Guidelines
- Test frameworks: `pytest` for CI‑friendly UI tests.
- Manual demos: run modules under `test/` to verify behavior changes.
- Test names: files `test_*.py`, functions `test_*`. Prefer small, focused assertions.
- Coverage: prioritize core widgets, behaviors, and `base_mvc` logic.
- Dev frameworks: `kivymd-production-fork` is a priority for UI components. It locates at `.venv/Lib/site-packages/kivymd` and must be read before implementing any new widget.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject, optional body. Examples: `Add headless-kivy`, `Update imports`, `Fix icon_button hover state`.
- PRs: clear description, linked issues (`Fixes #123`), screenshots or short clips for UI changes, steps to reproduce/verify, and notes on migration/compat.
- Checks: run `black`, and relevant demos/tests before requesting review.

## Security & Configuration Tips
- Do not commit local envs (`.venv/`) or large assets; follow `.gitignore`.
- Pin external forks via `pyproject.toml`/`uv.lock`; avoid ad‑hoc edits in `site-packages`.
- Prefer `uv run` to ensure consistent env when invoking tools.
