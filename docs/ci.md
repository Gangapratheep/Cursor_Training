# CI

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

- Triggers: push to `main`/`master`, pull requests, and **workflow_dispatch** (Actions → Run workflow)
- Job installs `requirements.txt` (includes `psutil`, `paramiko`) and runs `pytest`
- Dummy `FLASK_SECRET_KEY` / `ADMIN_PASSWORD` for CI only
- `permissions: contents: read` — no deploy keys

Re-run checks from the PR Checks tab or via workflow_dispatch on GitHub Actions.
