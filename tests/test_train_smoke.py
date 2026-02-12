from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.scripts import train


def test_train_smoke_succeeds_with_config(capsys: Any) -> None:
    exit_code = train.main(
        ["--config", "tests/fixtures/modular_addition.yaml", "--epochs", "1"]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["kind"] == "TRAIN_SMOKE"
    assert payload["status"] == "ok"
    assert payload["epochs"] == 1
    assert payload["config_path"] == "tests/fixtures/modular_addition.yaml"
    assert isinstance(payload["config_sha256"], str)
    assert payload["config_sha256"]


def test_train_smoke_fails_when_config_missing(tmp_path: Path, capsys: Any) -> None:
    missing = tmp_path / "missing.yaml"
    exit_code = train.main(["--config", str(missing)])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["kind"] == "ERROR"
    assert payload["error"]["type"] == "CONFIG_NOT_FOUND"
