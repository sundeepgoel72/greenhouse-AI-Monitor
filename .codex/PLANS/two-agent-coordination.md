# Two-Agent Coordination Plan

Use this repo with two roles sharing one checkout:

- Developer:
  implements backend/frontend changes, tests, and task/status updates
- Debugger:
  validates runtime behavior, deployment state, sensor/image ingestion findings, and handoff notes

Workflow:

1. Claim backend, frontend, docs, or deployment scope in `STATUS.md`.
2. Record meaningful findings in `WORKLOG/`.
3. Archive substantial handoffs in `HANDOVERS/`.
4. Keep `HANDOVER.md` focused on current resume state.
