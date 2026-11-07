"""Fail when total coverage is below the stored baseline.

Usage: python coverage_gate.py coverage.json quality/coverage-baseline.json
"""

import json
import sys


def main() -> int:
    with open(sys.argv[1]) as f:
        covered = float(json.load(f)["totals"]["percent_covered"])
    with open(sys.argv[2]) as f:
        floor = float(json.load(f)["percent"])
    ok = covered + 1e-9 >= floor
    print(f"coverage {covered:.2f}% (floor {floor:.2f}%): {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
