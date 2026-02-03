"""Replay runner core loop."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Iterable, Protocol, Sequence


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a single agent action."""

    ok: bool
    error: str | None = None


class Environment(Protocol):
    """Deterministic environment interface."""

    def reset(
        self, init: Any, rng: random.Random
    ) -> Any:  # pragma: no cover - protocol
        ...

    def observe(self, state: Any) -> dict[str, Any]:  # pragma: no cover - protocol
        ...

    def validate_action(
        self, state: Any, agent_id: str, action: Any
    ) -> ValidationResult:  # pragma: no cover - protocol
        ...

    def step(
        self,
        state: Any,
        joint_action: dict[str, Any],
        exogenous_x_t: Any,
        rng: random.Random,
    ) -> tuple[Any, Any, Any, dict[str, Any]]:  # pragma: no cover - protocol
        ...


class Policy(Protocol):
    """Deterministic policy interface."""

    def act(self, obs: Any, ctx: dict[str, Any]) -> Any:  # pragma: no cover - protocol
        ...


class Metrics(Protocol):
    """Metrics interface for per-step contributions and aggregation."""

    def per_step(
        self,
        t: int,
        state_hash_pre: str,
        action: dict[str, Any],
        reward: Any,
        cost: Any,
        info: dict[str, Any],
    ) -> Any:  # pragma: no cover - protocol
        ...

    def aggregate(
        self, contribs_stream: Iterable[Any]
    ) -> Any:  # pragma: no cover - protocol
        ...


@dataclass(frozen=True)
class RunConfig:
    """Configuration for a deterministic replay run."""

    env: Environment
    policies: dict[str, Policy]
    metrics: Metrics
    trace: Sequence[Any]
    seed: int
    init: Any
    out: IO[str]
    run_dir: Path
    tee_path: Path | None = None


@dataclass(frozen=True)
class RunHandle:
    """Handle returned after a run completes or fails."""

    run_dir: Path
    log_bundle_sha256: str | None
    exit_code: int
    error_payload: dict[str, Any] | None


def state_hash(state: Any) -> str:
    """Return a deterministic hash for a JSON-serializable state."""

    payload = json.dumps(
        state, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_jsonl(out: IO[str], payload: dict[str, Any]) -> None:
    out.write(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    )
    out.write("\n")
    out.flush()


def _tee_writer(tee_path: Path) -> IO[str]:
    tee_path.parent.mkdir(parents=True, exist_ok=True)
    return tee_path.open("w", encoding="utf-8")


def run(config: RunConfig) -> RunHandle:
    """Run a deterministic replay over the provided trace."""

    rng = random.Random(config.seed)
    state = config.env.reset(config.init, rng)
    tee_stream: IO[str] | None = None
    if config.tee_path is not None:
        tee_stream = _tee_writer(config.tee_path)

    def emit(payload: dict[str, Any]) -> None:
        _write_jsonl(config.out, payload)
        if tee_stream is not None:
            _write_jsonl(tee_stream, payload)

    contribs: list[Any] = []
    seq = 0
    try:
        for t, exogenous in enumerate(config.trace):
            obs = config.env.observe(state)
            actions: dict[str, Any] = {}
            ctx_base = {"t": t}
            for agent_id in sorted(config.policies.keys()):
                action = config.policies[agent_id].act(obs[agent_id], ctx_base)
                actions[agent_id] = action
            validations: dict[str, ValidationResult] = {}
            for agent_id in sorted(actions.keys()):
                validations[agent_id] = config.env.validate_action(
                    state, agent_id, actions[agent_id]
                )
            invalid = [
                (agent_id, result.error)
                for agent_id, result in validations.items()
                if not result.ok
            ]
            if invalid:
                raise ValueError(f"invalid actions: {invalid}")
            next_state, reward, cost, info = config.env.step(
                state, actions, exogenous, rng
            )
            contrib = config.metrics.per_step(
                t, state_hash(state), actions, reward, cost, info
            )
            contribs.append(contrib)
            emit(
                {
                    "kind": "STEP",
                    "seq": seq,
                    "t": t,
                    "state_hash_pre": state_hash(state),
                    "actions": actions,
                    "reward": reward,
                    "cost": cost,
                }
            )
            seq += 1
            state = next_state
            if info.get("done") is True:
                break
        _ = config.metrics.aggregate(contribs)
    except Exception as exc:  # pylint: disable=broad-except
        error_payload = {
            "kind": "ERROR",
            "error": {"type": "RUN_FAILURE", "message": str(exc)},
        }
        emit(error_payload)
        if tee_stream is not None:
            tee_stream.close()
        return RunHandle(
            run_dir=config.run_dir,
            log_bundle_sha256=_hash_file(config.tee_path),
            exit_code=1,
            error_payload=error_payload,
        )

    if tee_stream is not None:
        tee_stream.close()
    return RunHandle(
        run_dir=config.run_dir,
        log_bundle_sha256=_hash_file(config.tee_path),
        exit_code=0,
        error_payload=None,
    )


def _hash_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
