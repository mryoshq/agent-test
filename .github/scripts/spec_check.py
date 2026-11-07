"""Check that every goal spec and its acceptance tests match.

For each goals/<goal>/spec.md:
  - criteria are headings "### AC<k>: ..." (k = 1, 2, ...);
  - tests are functions "def test_ac<k>_..." in tests/acceptance/<goal>/;
  - every criterion has at least one test, and every test belongs to a criterion.
A tests/acceptance/<goal>/ folder without a spec is an error too.

Usage: python .github/scripts/spec_check.py   (from the repository root)
"""

import pathlib
import re
import sys

AC_HEADING = re.compile(r"^###\s+AC(\d+)\s*:", re.MULTILINE)
AC_TEST = re.compile(r"^\s*(?:async\s+)?def\s+test_ac(\d+)_\w*\s*\(", re.MULTILINE)
ANY_TEST = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(", re.MULTILINE)


def main() -> int:
    root = pathlib.Path(".")
    problems: list[str] = []
    specs = {p.parent.name: p for p in sorted(root.glob("goals/*/spec.md"))}
    test_dirs = {p.name for p in root.glob("tests/acceptance/*") if p.is_dir()}

    for goal in sorted(test_dirs - set(specs)):
        problems.append(f"tests/acceptance/{goal}/ has no goals/{goal}/spec.md")

    for goal, spec in specs.items():
        criteria = {int(k) for k in AC_HEADING.findall(spec.read_text())}
        if not criteria:
            problems.append(f"{spec}: no '### AC<k>:' criteria found")
        tested: set[int] = set()
        for f in sorted(root.glob(f"tests/acceptance/{goal}/**/test_*.py")):
            text = f.read_text()
            tested |= {int(k) for k in AC_TEST.findall(text)}
            for name in ANY_TEST.findall(text):
                if not re.match(r"test_ac\d+_", name):
                    problems.append(f"{f}: {name} is not named test_ac<k>_<what>")
        for k in sorted(criteria - tested):
            problems.append(f"{goal}: AC{k} has no test named test_ac{k}_*")
        for k in sorted(tested - criteria):
            problems.append(f"{goal}: tests named test_ac{k}_* but the spec has no AC{k}")
        print(f"{goal}: {len(criteria)} criteria, {len(tested & criteria)} covered by tests")

    for p in problems:
        print(f"FAIL: {p}")
    if not specs and not test_dirs:
        print("no goals yet")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
