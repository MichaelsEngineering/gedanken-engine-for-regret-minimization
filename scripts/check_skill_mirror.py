from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


MIRRORS = [
    (
        Path(".agent/skills/core-claim-qa/SKILL.md"),
        Path("/home/qol/.codex/skills/core-claim-qa/SKILL.md"),
    ),
    (
        Path(".agent/skills/core-claim-qa/agents/openai.yaml"),
        Path("/home/qol/.codex/skills/core-claim-qa/agents/openai.yaml"),
    ),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check repo skill mirrors against ~/.codex skill files."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if any mirror target is missing.",
    )
    args = parser.parse_args()

    failed = False
    for left, right in MIRRORS:
        if not left.exists():
            print(f"MISSING_REPO:{left}")
            failed = True
            continue

        if not right.exists():
            print(f"MISSING_EXTERNAL:{right}")
            if args.strict:
                failed = True
            continue

        left_sha = _sha(left)
        right_sha = _sha(right)
        status = "MATCH" if left_sha == right_sha else "MISMATCH"
        if status == "MISMATCH":
            failed = True
        print(f"{status}:{left}:{right}:{left_sha}:{right_sha}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
