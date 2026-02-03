"""Scalarization stubs for analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deterministic_scalarize(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic scalarization result without mutating input."""
    return {"scalar_stub": True, "metrics_count": len(metrics)}
