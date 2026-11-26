# CI

Workflow file: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (present locally; push may require a GitHub PAT with **`workflow`** scope).

## Behavior

- Triggers: push to `main`/`master`, pull requests, and **workflow_dispatch**
- Installs `requirements.txt` (Flask, SQLAlchemy, Migrate, RESTful, Marshmallow, psutil, Paramiko, pytest, …)
- Runs **`pytest`** (`tests/test_auth.py`, `test_servers.py`, `test_metrics.py`)
- Dummy `FLASK_SECRET_KEY` / `ADMIN_PASSWORD` for CI only
- `permissions: contents: read` — no deploy keys
- Metrics tests mock psutil/SSH — no live external SSH in CI

## Re-run

PR Checks tab, or Actions → CI → **Run workflow** (`workflow_dispatch`).

## Local check

```bash
source venv/bin/activate
pip install -r requirements.txt
pytest
```

If the workflow file is only local, pushing it needs a GitHub PAT with **`workflow`** scope.

Kubernetes manifests under `deploy/k8s/` are **not** applied by this workflow; see [deploy.md](./deploy.md).
