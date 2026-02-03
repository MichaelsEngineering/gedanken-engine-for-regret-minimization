"""Metrics stubs for analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deterministic_metric(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic metric summary without mutating input."""
    return {"metric_stub": True, "state_size": len(state)}
