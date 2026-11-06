# agent-test: project rules

These are the rules for everyone who changes this repo, agents and humans.
Role steps (coder, reviewer, test-writer, auditor) live in each agent's own setup.
CLAUDE.md and GEMINI.md only import this file.

## Stack and layout

- Python 3.12 and FastAPI. Versions are pinned in `requirements.txt` (runtime) and `requirements-dev.txt` (tools).
- `main.py` holds `app`, which uvicorn serves (`uvicorn main:app`).
  - The convention is an app factory: `create_app()` builds a new app with fresh, empty state, and `app = create_app()`.
  - The first goal that adds state introduces `create_app()`; its spec says so.
- Logic lives in plain classes and functions (for example a store class in its own module).
  - Route functions only read the request, call that logic, and shape the response.
  - Reason: mutation testing skips decorated functions, so logic inside a route is never tested by it.
- New state (such as a store) is created inside `create_app()` and kept on `app.state`, never at module level.
- Test locations:
  - `test_*.py` at the root: unit tests;
  - `tests/e2e/`: tests over real HTTP against a running server (`E2E_BASE_URL`);
  - `tests/acceptance/<goal>/`: a goal's acceptance tests. Frozen.
- `goals/<goal>/spec.md`: a goal's definition of done. Frozen.

## Commands (exactly what CI runs)

```sh
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q -r requirements-dev.txt
export PY=/tmp/venv/bin/python
bash .github/scripts/check.sh all          # lint, types, unit tests + coverage floor, security, e2e
bash .github/scripts/check.sh lint         # or one step: lint | types | test | security | e2e
bash .github/scripts/check.sh acceptance <goal> -k "test_ac1_ or test_ac2_"   # your task's criteria
$PY -m ruff format .                       # format before you commit
```

## Rules for every change

- Change only what the task needs. Aim for under 200 changed lines. The merge gate rejects more than 400.
- No new dependencies. `requirements*.txt` is protected.
- Type hints on every new function. `mypy` must pass.
- Never use suppression comments, and never skip a test. Fix the cause instead.
  - Not allowed: `noqa`, `type: ignore`, `nosec`, `pragma: no cover`, `pragma: no branch`, `pragma: no mutate`, `ruff: noqa`, `mypy: ignore-errors`, `pyright: ignore`.
  - Not allowed: `pytest.mark.skip`, `skipif`, `xfail`, `pytest.skip(`, `importorskip`.
- App code never imports `pytest` and never checks whether it runs under a test.
- Tests:
  - add tests in NEW files (`test_<feature>.py`);
  - never edit, delete, rename, skip or weaken an existing test.
- Unit-test coverage (line + branch) must stay at or above `quality/coverage-baseline.json`.
- Acceptance tests and specs are frozen once merged. If one looks wrong, say so in your reply. Do not change it.

## Protected paths

The merge gate rejects any PR that touches these. Only the repo owner changes them.

- `.github/**`, `goals/**`, `tests/acceptance/**`, `harnessrouter/**`, `ai/**`, `quality/**`
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `requirements*.txt`, `pyproject.toml`, `setup.cfg`, `pytest.ini`, `tox.ini`, `noxfile.py`, `conftest.py` (anywhere)
- Tool configs: `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `pyrightconfig.json`, `.coveragerc`, `.bandit`, `.pre-commit-config.yaml`
- Python startup hooks: `sitecustomize.py`, `usercustomize.py`, `*.pth`
- `.gitattributes`
- `Dockerfile*`, `docker-compose*`, `.env*`, and deploy or tunnel config (cloudflared, wrangler, fly, vercel, k8s, terraform, nginx, ...)
- Existing test files: editing, deleting or renaming one is rejected. Adding a new test file is allowed.

## Git and pull requests

- Use the branch name the task gives. Never push to main, never force-push, never rebase a pushed branch.
- One task, one PR. The PR body contains `Resolves #<issue>`.
- Commit messages: `<type>: <what>`, for example `feat: add item store`.
