from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml


DEFAULT_FIXTURES_DIR = Path("traces/fixtures")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_fixture_files(fixtures_dir: Path) -> list[Path]:
    return sorted(
        [path for path in fixtures_dir.rglob("*") if path.is_file()],
        key=lambda path: path.as_posix(),
    )


def build_manifest(fixtures_dir: Path) -> dict[str, list[dict[str, str]]]:
    fixtures: list[dict[str, str]] = []
    for path in _iter_fixture_files(fixtures_dir):
        fixtures.append(
            {
                "path": path.as_posix(),
                "sha256": _hash_file(path),
            }
        )
    return {"fixtures": fixtures}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a YAML manifest of fixture file hashes."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help="Directory containing fixture files (default: traces/fixtures).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write manifest YAML (default: stdout).",
    )
    args = parser.parse_args()

    fixtures_dir = args.fixtures_dir
    if not fixtures_dir.exists():
        print(f"Fixtures directory not found: {fixtures_dir}", file=sys.stderr)
        return 2
    if not fixtures_dir.is_dir():
        print(f"Fixtures path is not a directory: {fixtures_dir}", file=sys.stderr)
        return 2

    manifest = build_manifest(fixtures_dir)
    payload = yaml.safe_dump(
        manifest,
        sort_keys=False,
    )

    if args.output is None:
        sys.stdout.write(payload)
    else:
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
