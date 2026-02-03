"""Fixture integrity tests for deterministic replay traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


FIXTURES_DIR = Path("traces/fixtures")
MANIFEST_PATH = FIXTURES_DIR / "manifest.sha256"


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _iter_manifest() -> list[tuple[str, Path]]:
    entries: list[tuple[str, Path]] = []
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel_path = line.split(None, 1)
        entries.append((digest, Path(rel_path)))
    return entries


def test_fixture_manifest_hashes_match() -> None:
    assert MANIFEST_PATH.exists(), "fixtures manifest missing"
    entries = _iter_manifest()
    assert entries, "fixtures manifest must list at least one file"
    for digest, rel_path in entries:
        full_path = Path(rel_path)
        assert full_path.exists(), f"fixture missing: {rel_path}"
        assert _sha256(full_path) == digest


def test_fixture_events_are_minimal_and_ordered() -> None:
    for _, rel_path in _iter_manifest():
        events: list[dict[str, object]] = []
        with Path(rel_path).open("r", encoding="utf-8") as handle:
            for line in handle:
                events.append(json.loads(line))
        assert events, f"fixture empty: {rel_path}"
        assert events[0]["kind"] == "TRACE_STARTED"
        trace_id = events[0]["trace_id"]
        last_seq = -1
        for event in events:
            for key in ("kind", "trace_id", "seq", "ts", "meta"):
                assert key in event
            assert event["trace_id"] == trace_id
            seq_value = event["seq"]
            assert isinstance(seq_value, (int, str))
            seq = int(seq_value)
            assert seq > last_seq
            last_seq = seq
