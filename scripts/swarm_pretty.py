from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable


def _extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "text" in value and isinstance(value["text"], str):
            return value["text"]
        for key in (
            "text",
            "input_text",
            "output_text",
            "content",
            "message",
            "item",
            "response",
            "output",
            "data",
        ):
            if key in value:
                extracted = _extract_text(value[key])
                if extracted:
                    return extracted
        return None
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            extracted = _extract_text(item)
            if extracted:
                parts.append(extracted)
        if parts:
            return " ".join(parts)
    return None


def _summarize_usage(usage: dict[str, Any]) -> str | None:
    if not usage:
        return None
    for key in ("total_tokens", "input_tokens", "output_tokens"):
        if key in usage and isinstance(usage[key], int):
            break
    else:
        return None
    pieces = []
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            pieces.append(f"{key}={value}")
    return "usage=" + ",".join(pieces) if pieces else None


def format_event(event: dict[str, Any], *, lane: str, max_len: int = 200) -> str:
    """Format a single JSONL event as a human-readable line."""
    event_type = event.get("type", "event")
    parts = [f"[{lane}] {event_type}"]

    item = event.get("item")
    if isinstance(item, dict):
        item_type = item.get("type")
        item_id = item.get("id")
        if isinstance(item_type, str):
            parts.append(f"item_type={item_type}")
        if isinstance(item_id, str):
            parts.append(f"item_id={item_id}")

    thread_id = event.get("thread_id")
    if isinstance(thread_id, str):
        parts.append(f"thread_id={thread_id}")

    usage = event.get("usage")
    if isinstance(usage, dict):
        usage_summary = _summarize_usage(usage)
        if usage_summary:
            parts.append(usage_summary)

    error = event.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message:
            parts.append(f"error={message}")

    text = _extract_text(event)
    if text:
        text = text.replace("\n", "\\n")
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        parts.append(text)

    return " ".join(parts)


def _iter_events(stream: Iterable[str]) -> Iterable[dict[str, Any]]:
    for line_number, line in enumerate(stream, start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            yield {"type": "raw.line", "line_number": line_number, "text": line.strip()}
            continue
        if isinstance(data, dict):
            yield data
        else:
            yield {"type": "raw.value", "line_number": line_number, "value": data}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pretty-print Codex JSONL events for terminal display."
    )
    parser.add_argument("--lane", required=True, help="Lane label (manager, agent1..)")
    args = parser.parse_args()

    for event in _iter_events(sys.stdin):
        if event.get("type") == "raw.line":
            text = event.get("text", "")
            sys.stdout.write(f"[{args.lane}] raw {text}\n")
        elif event.get("type") == "raw.value":
            sys.stdout.write(f"[{args.lane}] raw {event.get('value')}\n")
        else:
            sys.stdout.write(format_event(event, lane=args.lane) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
