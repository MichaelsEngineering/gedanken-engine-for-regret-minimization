"""Deterministic smoke-train entrypoint used by Makefile shortcuts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    """Build a minimal deterministic parser for smoke/train commands."""
    parser = argparse.ArgumentParser(prog="train", add_help=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--epochs", type=int, default=1)
    return parser


def _load_config(config_path: str | None) -> tuple[str | None, str | None]:
    if config_path is None:
        return None, None
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")
    text = path.read_text(encoding="utf-8")
    return str(path), _sha256_text(text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config_path, config_sha256 = _load_config(args.config)
    except FileNotFoundError as exc:
        error_payload = {
            "kind": "ERROR",
            "error": {
                "type": "CONFIG_NOT_FOUND",
                "message": str(exc),
                "status": 2,
            },
        }
        sys.stdout.write(
            json.dumps(error_payload, sort_keys=True, separators=(",", ":"))
        )
        sys.stdout.write("\n")
        return 2

    payload: dict[str, Any] = {
        "kind": "TRAIN_SMOKE",
        "status": "ok",
        "epochs": args.epochs,
        "config_path": config_path,
        "config_sha256": config_sha256,
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
