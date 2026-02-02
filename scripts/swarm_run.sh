#!/usr/bin/env bash
set -euo pipefail

# Resolve the repository root (git if available, otherwise current directory).
if REPO_ROOT="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  REPO_ROOT="${PWD}"
fi

# Prompts for manager and workers.
MANAGER_PROMPT='You are the Manager. Use specs/agent-orchestrator/spec.md and agent1.md through agent5.md. Coordinate workers and write manager_tasks.yaml and manager_verdict.yaml under runs/.'
AGENT_PROMPT_TEMPLATE='You are Agent %s. Follow specs/agent-orchestrator/agent%s.md and specs/agent-orchestrator/spec.md. Write output to runs/agent%s_out.yaml only.'

# Ensure required directories exist.
mkdir -p "${REPO_ROOT}/scripts" "${REPO_ROOT}/runs"

# Ensure codex is available.
if ! command -v codex >/dev/null 2>&1; then
  echo "error: codex not found on PATH" >&2
  exit 127
fi

# Route pretty output to the terminal when available.
TTY_OUT="/dev/stdout"
if [ -t 1 ]; then
  TTY_OUT="/dev/tty"
fi

# Per-lane JSONL logs for deterministic merging.
RUN_ID="${RUN_ID:-1}"
LANES=(manager agent1 agent2 agent3 agent4 agent5)
for lane in "${LANES[@]}"; do
  rm -f "${REPO_ROOT}/runs/run-${RUN_ID}-${lane}.jsonl"
done
rm -f "${REPO_ROOT}/runs/run-${RUN_ID}-swarm.jsonl"

# Launch manager and workers concurrently.
pids=()

(
  set -o pipefail
  codex exec --json "${MANAGER_PROMPT}" 2>&1 \
    | tee "${REPO_ROOT}/runs/run-${RUN_ID}-manager.jsonl" \
    | python "${REPO_ROOT}/scripts/swarm_pretty.py" --lane manager > "${TTY_OUT}"
) &
pids+=("$!")

for i in 1 2 3 4 5; do
  agent_prompt=$(printf "${AGENT_PROMPT_TEMPLATE}" "${i}" "${i}" "${i}")
  (
    set -o pipefail
    codex exec --json "${agent_prompt}" 2>&1 \
      | tee "${REPO_ROOT}/runs/run-${RUN_ID}-agent${i}.jsonl" \
      | python "${REPO_ROOT}/scripts/swarm_pretty.py" --lane "agent${i}" > "${TTY_OUT}"
  ) &
  pids+=("$!")
done

# Wait for all jobs; fail if any job fails.
status=0
for pid in "${pids[@]}"; do
  if ! wait "${pid}"; then
    status=1
  fi
done

merge_status=0
python "${REPO_ROOT}/scripts/swarm_merge_jsonl.py" --run-id "${RUN_ID}" --runs-dir "${REPO_ROOT}/runs" || merge_status=$?
if [ "${status}" -eq 0 ] && [ "${merge_status}" -ne 0 ]; then
  status="${merge_status}"
fi
exit "${status}"
