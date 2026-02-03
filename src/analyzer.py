"""Offline analyzer stubs for deterministic replay evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deterministic_stub(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic derived view without mutating the input state."""
    derived = dict(state)
    derived["_analyzer_stub"] = True
    return derived


def analyze(state: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze a state snapshot and return deterministic derived artifacts."""
    return deterministic_stub(state)
