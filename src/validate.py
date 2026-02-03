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
