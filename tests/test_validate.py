from __future__ import annotations

from src.validate import validate_replay_config, validate_trace_header


def test_validate_trace_header_missing_trace_started() -> None:
    errors = validate_trace_header([], tape_expected=False)
    assert any("TRACE_STARTED" in error for error in errors)


def test_validate_trace_header_missing_seed() -> None:
    events = [{"kind": "TRACE_STARTED", "trace_id": "t1", "seq": 0}]
    errors = validate_trace_header(events, tape_expected=False)
    assert any("seed" in error for error in errors)


def test_validate_trace_header_missing_tape_ref_when_requested() -> None:
    events = [{"kind": "TRACE_STARTED", "seed": 42}]
    errors = validate_trace_header(events, tape_expected=True)
    assert any("tape_ref" in error for error in errors)


def test_validate_replay_config_requires_seed_or_tape() -> None:
    errors = validate_replay_config({})
    assert any("seed or tape" in error for error in errors)


def test_validate_replay_config_requires_tape_ref() -> None:
    errors = validate_replay_config({"tape": "tape.jsonl"})
    assert any("tape_ref" in error for error in errors)


def test_validate_replay_config_rejects_seed_and_tape() -> None:
    errors = validate_replay_config({"seed": 7, "tape": "tape.jsonl"})
    assert any("both seed and tape" in error for error in errors)


def test_validate_replay_config_rejects_blank_tape_ref() -> None:
    errors = validate_replay_config({"tape": "tape.jsonl", "tape_ref": "  "})
    assert any("tape_ref" in error for error in errors)


def test_validate_trace_header_rejects_blank_tape_ref_when_requested() -> None:
    events = [{"kind": "TRACE_STARTED", "seed": 42, "tape_ref": "  "}]
    errors = validate_trace_header(events, tape_expected=True)
    assert any("tape_ref" in error for error in errors)
