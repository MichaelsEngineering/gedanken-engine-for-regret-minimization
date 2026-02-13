# Phase 3 Security and Supply Chain Review

## Snapshot
- Captured at (UTC): `2026-02-13`
- Branch: `main`
- Commit SHA: `9337832810bc04f7347a200914e5183f865b0ac1`

## 1) Dependency control review (`pyproject.toml` + `uv.lock`)

### Findings
- Runtime dependencies are declared in `pyproject.toml` and resolved/pinned in `uv.lock`:
  - `pydantic>=2.6` -> `2.12.5`
  - `pyyaml>=6.0` -> `6.0.3`
  - `rich>=13.7` -> `14.3.1`
- Dev dependencies are declared and pinned:
  - `mypy>=1.10` -> `1.19.1`
  - `pytest>=8.2` -> `9.0.2`
  - `pytest-cov>=5.0` -> `7.0.0`
  - `ruff>=0.6` -> `0.14.14`
  - `types-PyYAML>=6.0` -> `6.0.12.20250915`
- Lockfile footprint:
  - total packages: `25`
  - registry-resolved packages: `24`
  - editable local package: `1` (`source = { editable = "." }`)
- Lockfile captures artifact hashes and source URLs (`sdist` + `wheels`) for resolved packages.

### Security/supply-chain risk note
- `pyproject.toml` uses minimum-version specifiers (`>=`) rather than bounded or exact constraints. Reproducibility and supply-chain control currently rely on strict `uv.lock` usage discipline.

### Evidence artifact
- `plans/artifacts/phase3_dependency_control.tsv`

## 2) Runtime boundary controls

### Allowlisted import controls
- Replay CLI enforces module prefix allowlist:
  - `DEFAULT_ALLOWED_MODULE_PREFIXES = ("src", "tests")`
  - `_module_allowed(...)` gate before dynamic import
  - `_load_callable(...)` rejects non-allowlisted modules
- Deterministic negative-path behavior exists in tests (`tests/test_replay_cli.py`) for disallowed modules.

### Core loop network/time boundary checks
- `src/runner.py` core replay loop uses seeded RNG (`random.Random(config.seed)`) and deterministic ordering (`sorted(...)`).
- Static grep over `src/` found no imports of `requests`, `socket`, `http`, `urllib`, `time`, `datetime`, or `subprocess` in replay core paths.
- Conclusion: no hidden network/time dependencies identified in the replay core loop paths under `src/replay.py`, `src/runner.py`, and `src/replay_fixtures.py`.

## 3) CI/security enforcement gaps

### Observed gaps
- `.github/workflows/` exists but contains no workflow files.
- No `dependabot.yml` present.
- No automated security scanning hooks detected in repo automation/config surfaces (CodeQL, dependency audit tooling, secret scan tooling, SBOM, attestation).
- Current PR template is minimal and does not require explicit security-impact sections.

### Priority
- `HIGH`: missing workflow automation and enforceable status checks.
- `HIGH`: missing automated security scan pipeline.
- `MEDIUM`: missing automated dependency update process.
- `LOW`: PR template lacks explicit security/supply-chain checkboxes.

### Evidence artifact
- `plans/artifacts/phase3_ci_security_gaps.tsv`

## Phase 3 verdict
- Dependency locking: `PASS` (lockfile-based control is present and detailed).
- Runtime boundary controls: `PASS` (allowlist and deterministic/no-network-time core behavior confirmed).
- CI/security enforcement: `FAIL` for high-assurance baseline due to absent workflow automation and security scanning pipeline.
