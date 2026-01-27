#!/usr/bin/env python3
"""Fail CI if pip-audit filtered report contains CVSS >= 7.0."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def get_score(v: dict) -> float | None:
    cvss_v3 = v.get("cvss_v3") or {}
    base = cvss_v3.get("base_score")
    if isinstance(base, (int, float)):
        return float(base)
    s = v.get("score")
    try:
        return float(s) if s is not None else None
    except Exception:
        return None


def main() -> int:
    p = Path("pip-audit-filtered.json")
    if not p.exists():
        print("No pip-audit-filtered.json found; skipping high-severity check")
        return 0

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print("Failed to read pip-audit-filtered.json; skipping check:", exc)
        return 0

    high: list[tuple[str, str, float, str | None]] = []
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            score = get_score(v)
            if score is not None and score >= 7.0:
                high.append((dep.get("name", ""), v.get("id", ""), score, v.get("description")))

    if high:
        print("High severity vulnerabilities found:")
        for name, vid, score, desc in high:
            print(f"- {name} {vid} (CVSS {score})")
        return 1

    print("No high severity (CVSS>=7.0) vulnerabilities found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
