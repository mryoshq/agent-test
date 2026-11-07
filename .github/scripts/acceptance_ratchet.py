"""Acceptance ratchet: an acceptance test that passes on the base commit must still pass.

Before a goal is built most of its acceptance tests fail, so "all must pass" would block every
task. This only blocks going backwards. The merge gate checks each task's own tests, and
verify_goal checks the full suite at the end.

Usage: python acceptance_ratchet.py base.xml head.xml
A missing base.xml means there is no base (first push); a missing head.xml is an error.
"""

import os
import sys
import xml.etree.ElementTree as ET


def results(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        if case.find("failure") is not None:
            out[test_id] = "failed"
        elif case.find("error") is not None:
            out[test_id] = "error"
        elif case.find("skipped") is not None:
            out[test_id] = "skipped"
        else:
            out[test_id] = "passed"
    return out


def main() -> int:
    base_path, head_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(head_path):
        print(f"FAIL: {head_path} is missing (the acceptance run did not finish)")
        return 1
    head = results(head_path)
    base = results(base_path) if os.path.exists(base_path) else {}
    passed_base = {t for t, s in base.items() if s == "passed"}
    passed_head = {t for t, s in head.items() if s == "passed"}
    regressions = sorted(passed_base - passed_head)
    skipped = sorted(t for t, s in head.items() if s == "skipped")

    lines = [
        "### Acceptance tests",
        f"- this commit: {len(passed_head)}/{len(head)} pass",
        f"- base commit: {len(passed_base)}/{len(base)} pass",
        f"- regressions: {len(regressions)}",
    ]
    lines += [f"  - `{t}` ({head.get(t, 'missing')})" for t in regressions]
    if skipped:
        lines.append(f"- skipped (not allowed): {len(skipped)}")
        lines += [f"  - `{t}`" for t in skipped]
    text = "\n".join(lines)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(text + "\n")
    return 1 if regressions or skipped else 0


if __name__ == "__main__":
    sys.exit(main())
