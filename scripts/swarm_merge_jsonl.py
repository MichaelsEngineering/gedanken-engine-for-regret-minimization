from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

LANES = ("manager", "agent1", "agent2", "agent3", "agent4", "agent5")


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} invalid JSON") from exc
            if not isinstance(data, dict):
                raise ValueError(f"{path}:{line_number} JSONL entries must be objects")
            yield data


def merge_jsonl(run_id: str, runs_dir: Path, *, output_path: Path | None = None) -> tuple[Path, int]:
    if output_path is None:
        output_path = runs_dir / f"run-{run_id}-swarm.jsonl"

    total_entries = 0
    with output_path.open("w", encoding="utf-8") as out_handle:
        for lane in LANES:
            lane_path = runs_dir / f"run-{run_id}-{lane}.jsonl"
            if not lane_path.exists():
                raise FileNotFoundError(f"Missing lane log: {lane_path}")
            for entry in _iter_jsonl(lane_path):
                total_entries += 1
                if "lane" in entry and entry["lane"] != lane:
                    raise ValueError(
                        f"{lane_path}: lane field mismatch (found {entry['lane']})"
                    )
                entry["lane"] = lane
                out_handle.write(json.dumps(entry, separators=(",", ":")) + "\n")

    return output_path, total_entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge per-lane JSONL logs into a single swarm log."
    )
    parser.add_argument("--run-id", required=True, help="Run id, e.g. 1")
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Path to runs directory (default: runs)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for merged JSONL",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    output_path = Path(args.output) if args.output else None
    target = output_path or (runs_dir / f"run-{args.run_id}-swarm.jsonl")
    print(f"Merging JSONL lanes into {target}...", flush=True)
    output_path, total_entries = merge_jsonl(
        args.run_id, runs_dir, output_path=output_path
    )
    print(
        f"Merge complete for run {args.run_id}: {total_entries} entries -> {output_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
