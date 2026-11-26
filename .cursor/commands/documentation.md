# documentation

Update project documentation to match the current codebase.

1. Review `app.py`, `blueprints/`, `schemas/`, `metrics/`, `models.py`, `deploy/`, and routes in templates.
2. Refresh docs under `docs/` (`architecture.md`, `auth.md`, `servers.md`, `metrics.md`, `ui.md`, `ci.md`, `TODO.md`) and `README.md`.
3. Keep security notes accurate: session auth, no SSH secrets in HTML/JSON, localhost bind by default, fixed SSH commands.
4. Document API paths, run steps, how to run `pytest`, and Kubernetes deploy steps under `deploy/k8s/` when those files exist.
5. If `README.md` already exists, **update** it — do not wipe sections that are still accurate (overview, setup, usage, layout, docs index).
6. Do not invent application features that are not implemented.
