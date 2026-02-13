from __future__ import annotations

from src.validate import (
    validate_admissibility,
    validate_replay_config,
    validate_trace_header,
)


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


def test_validate_admissibility_rejects_oracle_mode() -> None:
    errors = validate_admissibility({"comparator_mode": "oracle"})
    assert any("inadmissible" in error for error in errors)


def test_validate_admissibility_rejects_hidden_and_future_info() -> None:
    errors = validate_admissibility(
        {"uses_hidden_state": True, "uses_future_info": True}
    )
    assert any("hidden state" in error for error in errors)
    assert any("future information" in error for error in errors)


def test_validate_admissibility_rejects_invalid_types() -> None:
    errors = validate_admissibility(
        {
            "comparator_mode": 1,
            "uses_hidden_state": "yes",
            "uses_future_info": "no",
        }
    )
    assert any("comparator_mode must be a string" in error for error in errors)
    assert any("uses_hidden_state must be a bool" in error for error in errors)
    assert any("uses_future_info must be a bool" in error for error in errors)


def test_validate_admissibility_accepts_admissible_record() -> None:
    errors = validate_admissibility(
        {
            "comparator_mode": "admissible",
            "uses_hidden_state": False,
            "uses_future_info": False,
        }
    )
    assert errors == []
