---
name: repo-workflow
description: Clone the agent-test repo, set git credentials, make the venv and run the same checks CI runs. Use at the start of every task in this repo and before every push.
---

# repo-workflow

1. Credentials, only when `$GITHUB_TOKEN` is set. Never print, echo or log the token.
   ```sh
   git config --global credential.helper '!f() { echo "username=x-access-token"; echo "password=$GITHUB_TOKEN"; }; f'
   ```
2. Clone and read the rules:
   ```sh
   git clone https://github.com/$REPO_SLUG.git repo && cd repo
   cat AGENTS.md
   ```
3. Make your own venv in your own folder. `/tmp` is shared with other sessions, each running as a different user.
   Shells do not keep variables, so run the first line again at the start of every later command (it also sets `PY`'s folder).
   ```sh
   export TMPDIR="/tmp/agent-$(id -u)"; mkdir -p -m 700 "$TMPDIR" && [ -O "$TMPDIR" ] || { echo "PRIVATE TMP FAILED"; exit 1; }
   python3 -m venv "$TMPDIR/venv" && "$TMPDIR/venv/bin/pip" install -q -r requirements-dev.txt
   export PY="$TMPDIR/venv/bin/python"
   ```
   If it prints PRIVATE TMP FAILED or "Permission denied", stop and report it. Never use a folder directly in `/tmp`.
4. Run the checks. They are the same commands CI runs. Each step prints PASS or FAIL.
   ```sh
   bash .github/scripts/check.sh all
   bash .github/scripts/check.sh acceptance <goal> -k "test_ac1_ or test_ac2_"
   ```
   Acceptance tests of criteria that are not in your task may fail. That is expected until other tasks land.
5. Before each push: `$PY -m ruff format .`, then step 4 again. Push only when every check passes.
6. Read failures before you change anything. Fix the cause. Never add a suppression comment or a skip.
