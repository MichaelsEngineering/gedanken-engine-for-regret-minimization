"""Fixture trace content tests for replay scaffolding."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURES_DIR = Path("traces/fixtures")
MANIFEST_PATH = FIXTURES_DIR / "manifest.sha256"


def _iter_fixture_paths() -> list[Path]:
    entries: list[Path] = []
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        _digest, rel_path = line.split(None, 1)
        entries.append(Path(rel_path))
    return entries


def test_fixture_trace_ids_match_filenames() -> None:
    for fixture_path in _iter_fixture_paths():
        events: list[dict[str, object]] = []
        with fixture_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                events.append(json.loads(line))
        assert events, f"fixture empty: {fixture_path}"
        trace_id = events[0]["trace_id"]
        assert trace_id == fixture_path.stem
