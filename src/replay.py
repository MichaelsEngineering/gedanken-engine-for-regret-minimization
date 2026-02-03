"""Replay CLI and wiring."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Never, Sequence

from src import runner

DEFAULT_ALLOWED_MODULE_PREFIXES = ("src", "tests")


@dataclass(frozen=True)
class CliConfig:
    """Parsed CLI configuration."""

    env_factory: Callable[[], runner.Environment]
    policies_factory: Callable[[], dict[str, runner.Policy]]
    metrics_factory: Callable[[], runner.Metrics]
    trace_path: Path
    seed: int | None
    tape_path: Path | None
    out_dir: Path
    tee: bool


class DeterministicArgumentParser(argparse.ArgumentParser):
    """Argument parser with deterministic error output."""

    def error(self, message: str) -> Never:
        self._emit_error("ARGPARSE_ERROR", message, 2)
        raise SystemExit(2)

    def exit(self, status: int = 0, message: str | None = None) -> Never:
        if status:
            self._emit_error("ARGPARSE_EXIT", message or "", status)
        raise SystemExit(status)

    @staticmethod
    def _emit_error(error_type: str, message: str, status: int) -> None:
        payload = {
            "kind": "ERROR",
            "error": {"type": error_type, "message": message, "status": status},
        }
        sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        sys.stdout.flush()


def build_parser() -> DeterministicArgumentParser:
    parser = DeterministicArgumentParser(prog="replay", add_help=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--policies", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--tape")
    parser.add_argument("--out", required=True)
    parser.add_argument("--tee", action="store_true")
    return parser


def _module_allowed(module_name: str, allowed_prefixes: Sequence[str]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in allowed_prefixes
    )


def _load_callable(
    path: str, *, allowed_prefixes: Sequence[str] = DEFAULT_ALLOWED_MODULE_PREFIXES
) -> Callable[[], Any]:
    if ":" not in path:
        raise ValueError("callable path must be of the form module:attr")
    module_name, attr = path.split(":", 1)
    if not _module_allowed(module_name, allowed_prefixes):
        raise ValueError(f"module {module_name} is not in the allowlist")
    module = import_module(module_name)
    target = getattr(module, attr)
    if not callable(target):
        raise TypeError(f"{path} is not callable")
    return target


def _load_jsonl(path: Path) -> list[Any]:
    items: list[Any] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def build_config(args: argparse.Namespace) -> CliConfig:
    return CliConfig(
        env_factory=_load_callable(args.env),
        policies_factory=_load_callable(args.policies),
        metrics_factory=_load_callable(args.metrics),
        trace_path=Path(args.trace),
        seed=args.seed,
        tape_path=Path(args.tape) if args.tape else None,
        out_dir=Path(args.out),
        tee=bool(args.tee),
    )


def _validate_args(config: CliConfig) -> None:
    if (config.seed is None) == (config.tape_path is None):
        raise ValueError("exactly one of --seed or --tape is required")


def _emit_validation_error(message: str) -> None:
    payload = {
        "kind": "ERROR",
        "error": {"type": "ARG_VALIDATION", "message": message, "status": 2},
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _trace_from_paths(trace_path: Path, tape_path: Path | None) -> list[Any]:
    trace_items = _load_jsonl(trace_path)
    if tape_path is None:
        return trace_items
    tape_items = _load_jsonl(tape_path)
    return tape_items


def _run_replay(config: CliConfig) -> runner.RunHandle:
    env = config.env_factory()
    policies = config.policies_factory()
    metrics = config.metrics_factory()
    trace = _trace_from_paths(config.trace_path, config.tape_path)
    tee_path = config.out_dir / "events.jsonl" if config.tee else None
    run_config = runner.RunConfig(
        env=env,
        policies=policies,
        metrics=metrics,
        trace=trace,
        seed=config.seed if config.seed is not None else 0,
        init={},
        out=sys.stdout,
        run_dir=config.out_dir,
        tee_path=tee_path,
    )
    return runner.run(run_config)


def main(argv: Sequence[str] | None = None) -> int:
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
    try:
        config = build_config(args)
        _validate_args(config)
    except Exception as exc:  # pylint: disable=broad-except
        _emit_validation_error(str(exc))
        return 2
    handle = _run_replay(config)
    return handle.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
