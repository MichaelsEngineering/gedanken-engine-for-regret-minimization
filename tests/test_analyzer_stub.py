from __future__ import annotations

from copy import deepcopy

from src import analyzer
from src.metrics import deterministic_metric
from src.scalarization import deterministic_scalarize


def test_analyzer_modules_importable() -> None:
    assert analyzer.analyze({"x": 1})["_analyzer_stub"] is True
    assert deterministic_metric({"x": 1})["metric_stub"] is True
    assert deterministic_scalarize({"metric_stub": True})["scalar_stub"] is True


def test_deterministic_stub_no_mutation() -> None:
    state = {"x": 1}
    original = deepcopy(state)

    first = analyzer.deterministic_stub(state)
    second = analyzer.deterministic_stub(state)

    assert state == original
    assert first == second
    assert first is not state


def test_analyze_no_mutation() -> None:
    state = {"y": 2}
    original = deepcopy(state)

    result = analyzer.analyze(state)

    assert state == original
    assert result["_analyzer_stub"] is True
    assert result is not state
