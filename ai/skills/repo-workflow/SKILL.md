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
3. Make your own venv. The shared one is read-only.
   ```sh
   python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q -r requirements-dev.txt
   export PY=/tmp/venv/bin/python
   ```
4. Run the checks. They are the same commands CI runs. Each step prints PASS or FAIL.
   ```sh
   bash .github/scripts/check.sh all
   bash .github/scripts/check.sh acceptance <goal> -k "test_ac1_ or test_ac2_"
   ```
   Acceptance tests of criteria that are not in your task may fail. That is expected until other tasks land.
5. Before each push: `$PY -m ruff format .`, then step 4 again. Push only when every check passes.
6. Read failures before you change anything. Fix the cause. Never add a suppression comment or a skip.
