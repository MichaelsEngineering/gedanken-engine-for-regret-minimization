"""Validation helpers for replay configuration and trace headers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


TRACE_STARTED_KIND = "TRACE_STARTED"


def _has_nonblank_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _get_field(config: Mapping[str, Any] | object, name: str) -> Any:
    if isinstance(config, Mapping):
        return config.get(name)
    return getattr(config, name, None)


def validate_replay_config(config: Mapping[str, Any] | object) -> list[str]:
    """Validate a replay config for seed/tape requirements."""
    errors: list[str] = []
    seed = _get_field(config, "seed")
    tape = _get_field(config, "tape")
    tape_ref = _get_field(config, "tape_ref")

    has_seed = seed is not None
    if isinstance(tape, str):
        has_tape = bool(tape.strip())
    else:
        has_tape = bool(tape)

    if not has_seed and not has_tape:
        errors.append("Replay config must include seed or tape.")
    if has_seed and has_tape:
        errors.append("Replay config must not include both seed and tape.")
    if has_tape and not _has_nonblank_str(tape_ref):
        errors.append("Replay config must include tape_ref when tape is requested.")
    return errors


def validate_trace_header(
    events: Sequence[Mapping[str, Any]], *, tape_expected: bool
) -> list[str]:
    """Validate trace header invariants for replay determinism."""
    errors: list[str] = []
    if not events:
        errors.append(f"Trace is empty; first event must be {TRACE_STARTED_KIND}.")
        return errors
    first = events[0]
    if not isinstance(first, Mapping):
        errors.append("TraceStarted event must be a mapping.")
        return errors

    if first.get("kind") != TRACE_STARTED_KIND:
        errors.append(f"First event must be {TRACE_STARTED_KIND}.")
    if first.get("seed") is None:
        errors.append("TraceStarted.seed is required.")
    if tape_expected and not _has_nonblank_str(first.get("tape_ref")):
        errors.append("TraceStarted.tape_ref is required when tape is requested.")
    return errors


def validate_admissibility(record: Mapping[str, Any]) -> list[str]:
    """Validate comparator admissibility inputs for offline attribution."""
    errors: list[str] = []
    comparator_mode = record.get("comparator_mode")
    if comparator_mode is not None:
        if not isinstance(comparator_mode, str):
            errors.append("comparator_mode must be a string when provided.")
        elif comparator_mode == "oracle":
            errors.append("oracle comparator mode is inadmissible.")
        elif comparator_mode != "admissible":
            errors.append("comparator_mode must be 'admissible' or 'oracle'.")

    uses_hidden_state = record.get("uses_hidden_state")
    if uses_hidden_state is not None:
        if not isinstance(uses_hidden_state, bool):
            errors.append("uses_hidden_state must be a bool when provided.")
        elif uses_hidden_state:
            errors.append("comparator must not use hidden state.")

    uses_future_info = record.get("uses_future_info")
    if uses_future_info is not None:
        if not isinstance(uses_future_info, bool):
            errors.append("uses_future_info must be a bool when provided.")
        elif uses_future_info:
            errors.append("comparator must not use future information.")
    return errors
