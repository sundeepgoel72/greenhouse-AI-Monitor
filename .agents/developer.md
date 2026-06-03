# Developer Agent Role

Own:

- backend and frontend implementation
- tests and build validation
- schema, API, and UI changes
- updates to `.codex/TASK.md` and `.codex/STATUS.md`

Before editing:

1. Claim scope in `.codex/STATUS.md`.
2. Create a lock file in `.agents/locks/` for shared areas such as `backend`, `frontend`, or `deploy`.

Do not:

- change operational behavior without recording validation steps
- overlap active deployment/debugging work without a clear handoff
