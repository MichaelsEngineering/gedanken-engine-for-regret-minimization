"""Deterministic metric helpers for dimensionless regret analysis."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeGuard

TIME_UNITS = frozenset({"ms", "s"})
SUPPORTED_UNITS = frozenset({"ms", "s", "count", "ratio", "dimensionless"})
INVARIANCE_TOLERANCE = 1e-12


def _is_number(value: Any) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _convert_time_value(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return value
    if from_unit == "ms" and to_unit == "s":
        return value / 1000.0
    if from_unit == "s" and to_unit == "ms":
        return value * 1000.0
    raise ValueError(f"unsupported conversion {from_unit}->{to_unit}")


def deterministic_metric(metric: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one metric record and compute normalized component regret."""
    errors: list[str] = []

    name = metric.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    unit_value = metric.get("unit")
    unit = unit_value if isinstance(unit_value, str) else ""
    if unit not in SUPPORTED_UNITS:
        errors.append(f"unit must be one of {sorted(SUPPORTED_UNITS)}")

    candidate = metric.get("candidate_value")
    comparator = metric.get("comparator_value")
    scale = metric.get("scale_c_i")
    weight = metric.get("weight")

    if not _is_number(candidate):
        errors.append("candidate_value must be numeric")
    if not _is_number(comparator):
        errors.append("comparator_value must be numeric")
    if not _is_number(scale):
        errors.append("scale_c_i must be numeric")
    if not _is_number(weight):
        errors.append("weight must be numeric")

    if _is_number(scale) and float(scale) <= 0.0:
        errors.append("scale_c_i must be > 0")
    if _is_number(weight) and float(weight) < 0.0:
        errors.append("weight must be >= 0")

    if errors:
        return {"valid": False, "errors": errors}

    assert isinstance(name, str)
    assert _is_number(candidate)
    assert _is_number(comparator)
    assert _is_number(scale)
    assert _is_number(weight)
    candidate_f = float(candidate)
    comparator_f = float(comparator)
    scale_f = float(scale)
    weight_f = float(weight)
    r_i = (comparator_f - candidate_f) / scale_f
    unit_invariance_pass = True
    invariance_error: str | None = None

    if unit in TIME_UNITS:
        alt_unit = metric.get("alt_unit")
        if alt_unit is None:
            alt_unit = "s" if unit == "ms" else "ms"
            alt_candidate = _convert_time_value(candidate_f, unit, alt_unit)
            alt_comparator = _convert_time_value(comparator_f, unit, alt_unit)
            alt_scale = _convert_time_value(scale_f, unit, alt_unit)
        else:
            if not isinstance(alt_unit, str) or alt_unit not in TIME_UNITS:
                return {"valid": False, "errors": ["alt_unit must be 'ms' or 's'"]}
            alt_candidate_raw = metric.get("candidate_value_in_alt_unit")
            alt_comparator_raw = metric.get("comparator_value_in_alt_unit")
            alt_scale_raw = metric.get("scale_c_i_in_alt_unit")
            if not _is_number(alt_candidate_raw):
                return {
                    "valid": False,
                    "errors": ["candidate_value_in_alt_unit must be numeric"],
                }
            if not _is_number(alt_comparator_raw):
                return {
                    "valid": False,
                    "errors": ["comparator_value_in_alt_unit must be numeric"],
                }
            if not _is_number(alt_scale_raw):
                return {
                    "valid": False,
                    "errors": ["scale_c_i_in_alt_unit must be numeric"],
                }
            alt_candidate = float(alt_candidate_raw)
            alt_comparator = float(alt_comparator_raw)
            alt_scale = float(alt_scale_raw)
            if alt_scale <= 0.0:
                return {"valid": False, "errors": ["scale_c_i_in_alt_unit must be > 0"]}

        alt_r_i = (alt_comparator - alt_candidate) / alt_scale
        if abs(r_i - alt_r_i) > INVARIANCE_TOLERANCE:
            unit_invariance_pass = False
            invariance_error = (
                f"unit invariance failed for {name}: "
                f"canonical={r_i:.16g} alternate={alt_r_i:.16g}"
            )

    return {
        "valid": True,
        "errors": [],
        "name": name.strip(),
        "unit": unit,
        "scale_c_i": scale_f,
        "weight": weight_f,
        "r_i": r_i,
        "dimensionless": True,
        "unit_invariance_pass": unit_invariance_pass,
        "invariance_error": invariance_error,
    }
