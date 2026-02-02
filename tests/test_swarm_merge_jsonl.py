from __future__ import annotations

import json
from pathlib import Path

from scripts.swarm_merge_jsonl import merge_jsonl


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


def test_merge_jsonl_adds_lane_and_orders(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    run_id = "1"
    lanes = [
        ("manager", [{"type": "thread.started"}, {"type": "turn.started"}]),
        ("agent1", [{"type": "thread.started"}]),
        ("agent2", [{"type": "thread.started"}]),
        ("agent3", [{"type": "thread.started"}]),
        ("agent4", [{"type": "thread.started"}]),
        ("agent5", [{"type": "thread.started"}]),
    ]
    for lane, entries in lanes:
        _write_jsonl(runs_dir / f"run-{run_id}-{lane}.jsonl", entries)

    output_path, _ = merge_jsonl(run_id, runs_dir)

    merged = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["lane"] for entry in merged[:2]] == ["manager", "manager"]
    assert merged[2]["lane"] == "agent1"
    assert merged[3]["lane"] == "agent2"
    assert merged[4]["lane"] == "agent3"
    assert merged[5]["lane"] == "agent4"
    assert merged[6]["lane"] == "agent5"
