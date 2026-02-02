from __future__ import annotations

from scripts.swarm_pretty import format_event


def test_format_event_includes_lane_and_type() -> None:
    event = {"type": "thread.started", "thread_id": "abc123"}
    line = format_event(event, lane="manager")
    assert line.startswith("[manager] thread.started")
    assert "thread_id=abc123" in line


def test_format_event_extracts_text() -> None:
    event = {
        "type": "message.output",
        "message": {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world"},
            ]
        },
    }
    line = format_event(event, lane="agent1")
    assert "[agent1] message.output" in line
    assert "hello world" in line


def test_format_event_extracts_item_text() -> None:
    event = {
        "type": "item.completed",
        "item": {"id": "item_2", "type": "reasoning", "text": "Preparing to review"},
    }
    line = format_event(event, lane="manager")
    assert "[manager] item.completed" in line
    assert "item_type=reasoning" in line
    assert "item_id=item_2" in line
    assert "Preparing to review" in line
