# Skills Notice

These skills are experimental drafts and are shared here for development purposes only.

Please do not redistribute, mirror, or republish them without explicit permission.

If you want to use or share these skills, contact me directly first. Otherwise, please wait until this repository reaches a stable version, at which point I will publish approved skills.

Consensus per facta concludentia.

$1.00 per user per month for sites such as `skills.lc` or similar. No warranty, express or implied.

## CLI packaging best practices

- Package mode is enabled via `tool.uv.package = true` in `pyproject.toml`.
- Keep a valid PEP 517 backend in `pyproject.toml` (`[build-system]` with setuptools/wheel) so entry points install predictably.
- Keep CLI entry points in `[project.scripts]` mapped to importable callables with signature `main(argv: Sequence[str] | None = None) -> int`.
- Verify after dependency sync:
  - `uv sync --dev`
  - `uv run rc --help`
- If CLI module paths change, update `[project.scripts]` in the same commit.
