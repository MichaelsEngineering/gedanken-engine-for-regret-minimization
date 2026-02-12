"""Deterministic scalarization helpers for normalized regret components."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def aggregate_dimensionless_regret(components: Iterable[Mapping[str, Any]]) -> float:
    """Aggregate dimensionless components with a weighted sum."""
    aggregate = 0.0
    for component in components:
        r_i = component.get("r_i")
        weight = component.get("weight")
        if not isinstance(r_i, (int, float)) or isinstance(r_i, bool):
            raise ValueError("component r_i must be numeric")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError("component weight must be numeric")
        if float(weight) < 0.0:
            raise ValueError("component weight must be >= 0")
        aggregate += float(weight) * float(r_i)
    return aggregate


def deterministic_scalarize(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Scalarize metrics payload via deterministic weighted-sum aggregation."""
    components = metrics.get("components")
    if not isinstance(components, list):
        return {
            "valid": False,
            "errors": ["components must be a list"],
            "aggregate_regret": None,
        }
    try:
        aggregate = aggregate_dimensionless_regret(components)
    except ValueError as exc:
        return {"valid": False, "errors": [str(exc)], "aggregate_regret": None}
    return {"valid": True, "errors": [], "aggregate_regret": aggregate}
