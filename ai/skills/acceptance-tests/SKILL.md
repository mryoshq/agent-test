---
name: acceptance-tests
description: How acceptance tests work in agent-test (goals/<goal>/spec.md plus tests/acceptance/<goal>/), covering naming, fixtures, e2e tests, and how to run the ones your task owns. Use when writing, running, reviewing or auditing acceptance tests.
---

# acceptance-tests

## How a goal is defined

- `goals/<goal>/spec.md` lists criteria as headings `### AC<k>: <title>`. Each one says how it is verified.
- `tests/acceptance/<goal>/test_<goal>*.py` has the tests. They are written from the spec only, before the code exists.
- Both are frozen once merged. A PR that changes them is rejected.
- CI's `spec_check.py` requires that every criterion has at least one test and that every test belongs to a criterion.

## Writing rules (test-writer)

- Name every test `test_ac<k>_<what>`. `k` is the criterion number. Never add a test without that prefix.
- Import app code only inside a fixture. Then every test is collected even before the code exists, and each test fails on its own.
  ```python
  import os
  import uuid

  import httpx
  import pytest
  from fastapi.testclient import TestClient


  @pytest.fixture
  def client() -> TestClient:
      from main import create_app  # imported here on purpose

      return TestClient(create_app())  # new app, empty storage, for every test


  def test_ac1_create_returns_201(client: TestClient) -> None:
      response = client.post("/items", json={"name": "pen", "price": 1.5})
      assert response.status_code == 201


  @pytest.mark.e2e
  def test_ac9_e2e_create_then_read() -> None:
      name = f"e2e-{uuid.uuid4().hex}"  # the server is shared, so use unique data
      with httpx.Client(base_url=os.environ["E2E_BASE_URL"], timeout=10) as http:
          ...
  ```
- Assert only what the spec states. If the spec allows a range, accept the whole range.
- No `skip`, `xfail`, `sleep`, random data without a fixed seed, real clocks, or test-order dependence.
- No network except `E2E_BASE_URL` in tests marked `e2e`.
- Put fixtures in the test module. `conftest.py` is protected, and adding one is rejected.
- Use only packages already in `requirements-dev.txt`.

## Running

```sh
export TMPDIR="/tmp/agent-$(id -u)"; mkdir -p -m 700 "$TMPDIR" && [ -O "$TMPDIR" ] || { echo "PRIVATE TMP FAILED"; exit 1; }
export PY="$TMPDIR/venv/bin/python"                                          # venv from repo-workflow
bash .github/scripts/check.sh acceptance <goal>                              # all criteria
bash .github/scripts/check.sh acceptance <goal> -k "test_ac1_ or test_ac3_"  # only yours
```

`check.sh` starts uvicorn and sets `E2E_BASE_URL` for tests marked `e2e`.
`-k "test_ac1_"` does not match `test_ac10_`.

## How results are judged

- On every PR, CI runs the acceptance tests on the PR and on its base. A test that passed on the base must still pass. Skips are not allowed.
- The merge gate requires every test of the task's own criteria to pass.
- When a goal's tasks are all merged, the lead runs the full suite, mutation testing and an independent audit of the code against the spec.
