"""Offline analyzer for dimensionless normalized regret."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.metrics import deterministic_metric
from src.scalarization import aggregate_dimensionless_regret


def _invalid_result(
    errors: list[str], components: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "valid": False,
        "errors": errors,
        "components": components or [],
        "aggregate_regret": None,
        "dimensionless": False,
        "unit_invariance_pass": False,
    }


def analyze(state: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze metric records and compute dimensionless aggregate regret."""
    metrics_obj = state.get("metrics")
    if not isinstance(metrics_obj, list):
        return _invalid_result(["metrics list is required"])
    if not metrics_obj:
        return _invalid_result(["metrics list must not be empty"])

    components: list[dict[str, Any]] = []
    errors: list[str] = []
    unit_invariance_pass = True

    for index, item in enumerate(metrics_obj):
        if not isinstance(item, Mapping):
            errors.append(f"metrics[{index}] must be an object")
            continue
        metric_result = deterministic_metric(item)
        if not metric_result.get("valid", False):
            for error in metric_result.get("errors", []):
                errors.append(f"metrics[{index}]: {error}")
            continue

        component = {
            "name": metric_result["name"],
            "r_i": metric_result["r_i"],
            "unit": metric_result["unit"],
            "scale_c_i": metric_result["scale_c_i"],
            "weight": metric_result["weight"],
        }
        components.append(component)

        if metric_result.get("unit_invariance_pass") is False:
            unit_invariance_pass = False
            invariance_error = metric_result.get("invariance_error")
            if isinstance(invariance_error, str) and invariance_error:
                errors.append(invariance_error)
            else:
                errors.append(f"unit invariance failed for {metric_result['name']}")

    if errors:
        return _invalid_result(errors, components)
    if not unit_invariance_pass:
        return _invalid_result(["unit invariance failed"], components)

    try:
        aggregate = aggregate_dimensionless_regret(components)
    except ValueError as exc:
        return _invalid_result([str(exc)], components)

    return {
        "valid": True,
        "errors": [],
        "components": components,
        "aggregate_regret": aggregate,
        "dimensionless": True,
        "unit_invariance_pass": True,
    }
