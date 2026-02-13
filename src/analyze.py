"""Offline analyzer CLI that emits deterministic report.json artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Never

from src import validation_engine


class DeterministicArgumentParser(argparse.ArgumentParser):
    """Argument parser with deterministic error output."""

    def error(self, message: str) -> Never:
        _emit_error("ARGPARSE_ERROR", message, 2)
        raise SystemExit(2)

    def exit(self, status: int = 0, message: str | None = None) -> Never:
        if status:
            _emit_error("ARGPARSE_EXIT", message or "", status)
        raise SystemExit(status)


def _emit_error(error_type: str, message: str, status: int) -> None:
    payload = {
        "kind": "ERROR",
        "error": {"type": error_type, "message": message, "status": status},
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def build_parser() -> DeterministicArgumentParser:
    parser = DeterministicArgumentParser(prog="analyze", add_help=True)
    parser.add_argument("--in", dest="events_path", required=True)
    parser.add_argument("--out", dest="report_path", required=True)
    parser.add_argument("--run-id")
    return parser


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL at line {line_number}: {exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                raise ValueError(f"event at line {line_number} must be an object")
            events.append(item)
    return events


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_deterministic_input(events: list[dict[str, Any]]) -> bool:
    seq_values: list[int] = []
    for event in events:
        if "seq" not in event:
            continue
        seq = event["seq"]
        if not isinstance(seq, int):
            return False
        seq_values.append(seq)
    return seq_values == sorted(seq_values) and len(seq_values) == len(set(seq_values))


def _derive_run_id(
    provided_run_id: str | None, events_path: Path, report_path: Path
) -> str:
    if provided_run_id is not None and provided_run_id.strip():
        return provided_run_id.strip()
    if report_path.name == "report.json":
        return report_path.parent.name
    return events_path.parent.name


def _report_payload(
    events_path: Path, report_path: Path, run_id: str | None
) -> dict[str, Any]:
    events = _read_events(events_path)
    scalar_summary = validation_engine.analyze(_analyzer_input_from_events(events))

    return {
        "report_version": "1",
        "run_id": _derive_run_id(run_id, events_path, report_path),
        "source_events_path": str(events_path),
        "source_events_sha256": _sha256_file(events_path),
        "event_count": len(events),
        "analysis": {
            "deterministic_input_valid": _is_deterministic_input(events),
            "scalar_summary": scalar_summary,
        },
    }


def _analyzer_input_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    admissibility_keys = (
        "comparator_mode",
        "uses_hidden_state",
        "uses_future_info",
    )

    def _merge_input(source: Mapping[str, Any], metrics: list[Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {"metrics": metrics}
        for key in admissibility_keys:
            if key in source:
                payload[key] = source[key]
        return payload

    for event in reversed(events):
        metrics = event.get("metrics")
        if isinstance(metrics, list):
            return _merge_input(event, metrics)
        analysis_input = event.get("analysis_input")
        if isinstance(analysis_input, Mapping):
            nested_metrics = analysis_input.get("metrics")
            if isinstance(nested_metrics, list):
                return _merge_input(analysis_input, nested_metrics)
    # Explicitly invalid when no metric data exists in the event stream.
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1

    events_path = Path(args.events_path)
    report_path = Path(args.report_path)
    run_id = args.run_id

    try:
        payload = _report_payload(events_path, report_path, run_id)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception as exc:  # pylint: disable=broad-except
        _emit_error("ARG_VALIDATION", str(exc), 2)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
