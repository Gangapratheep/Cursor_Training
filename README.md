# DemoMonitor

## Overview

DemoMonitor is a **local Flask + SQLite** demo that shows read-only Linux server metrics in a browser so you do not need to SSH in just to check CPU, memory, network, and listening ports.

- Sign in as a single admin user (hashed password, session cookie)
- Add / edit / delete Linux hosts (local via `psutil`, remote via SSH/Paramiko)
- Live dashboard cards and per-server detail with ~10s auto-refresh
- JSON metrics API for the UI (`/api/servers/...`)

Primary day-to-day use is on your laptop (`python app.py` on `127.0.0.1`). Kubernetes packaging below is optional for demos/labs.

## Setup / installation

```bash
git clone <your-fork-or-clone-url>
cd Monitoring_Application

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: FLASK_SECRET_KEY and ADMIN_PASSWORD
```

Optional database migrations:

```bash
export FLASK_APP=app.py
flask db upgrade
```

On first run the app also calls `db.create_all()` and seeds `admin` if missing.

### Environment

| Variable | Purpose | Default |
|----------|---------|---------|
| `FLASK_SECRET_KEY` | Session signing | `demo-dev-secret` |
| `ADMIN_PASSWORD` | Seeded admin password (stored hashed) | `admin123` |
| `FLASK_ENV` | Config profile | `development` |
| `BIND_HOST` | Listen address | `127.0.0.1` |
| `BIND_PORT` | Listen port | `5000` |

## Usage

### Start locally

```bash
source venv/bin/activate
python app.py
# → http://127.0.0.1:5000
```

Sign in: **`admin`** / value of `ADMIN_PASSWORD`.

### Typical workflow

1. Open the dashboard → **Add server**
2. For this machine: auth type **local**, hostname `127.0.0.1`
3. For a remote Linux host: auth **password** or **key**, username, and secret/key path
4. Watch live metrics on the dashboard (auto-refresh ~10s) or open **Details**
5. Use **Refresh now** anytime; **Edit** / **Delete** from the card

### API examples (after login cookie)

```bash
# Batch metrics (dashboard)
curl -b cookies.txt -c cookies.txt -X POST -d 'username=admin&password=admin123' \
  http://127.0.0.1:5000/login
curl -b cookies.txt http://127.0.0.1:5000/api/servers/metrics

# One server
curl -b cookies.txt http://127.0.0.1:5000/api/servers/1/metrics
```

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/servers/metrics` | Batch metrics for all servers |
| GET | `/api/servers/<id>/metrics` | Metrics for one server |

Both require a session. Responses never include SSH passwords or key material.

### Tests

```bash
pytest
# or:
pytest tests/test_auth.py tests/test_servers.py tests/test_metrics.py
```

## Deploy on Kubernetes

Manifests live under [`deploy/k8s/`](deploy/k8s/). Image build uses the root [`Dockerfile`](Dockerfile) (Gunicorn on `0.0.0.0:5000`).

> **Note:** The app is designed as a single-replica demo with SQLite on a PVC. Do not scale replicas above 1 without moving to a shared database.

### 1. Build and load the image

```bash
# Build
docker build -t demomonitor:latest .

# Kind
kind load docker-image demomonitor:latest

# Or Minikube
minikube image load demomonitor:latest

# Or push to your registry and set image: in deployment.yaml
# docker tag demomonitor:latest <registry>/demomonitor:latest
# docker push <registry>/demomonitor:latest
```

### 2. Edit secrets

Update [`deploy/k8s/secret.yaml`](deploy/k8s/secret.yaml) with strong `FLASK_SECRET_KEY` and `ADMIN_PASSWORD` (do not commit real values).

### 3. Apply manifests

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secret.yaml
kubectl apply -f deploy/k8s/pvc.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
# Optional Ingress (needs an ingress controller):
kubectl apply -f deploy/k8s/ingress.yaml
```

### 4. Access the app

```bash
# Port-forward (no Ingress required)
kubectl -n demomonitor port-forward svc/demomonitor 8080:80
# → http://127.0.0.1:8080  (admin / your ADMIN_PASSWORD secret)
```

With Ingress, point DNS/`/etc/hosts` at your controller for `demomonitor.local` (see `ingress.yaml`).

### 5. Check status

```bash
kubectl -n demomonitor get pods,svc,ingress
kubectl -n demomonitor logs -l app=demomonitor -f
```

### 6. Tear down

```bash
kubectl delete namespace demomonitor
```

## Layout

| Path | Role |
|------|------|
| `app.py` | Application factory (`create_app`) |
| `config.py` / `extensions.py` | Config objects; `db` + Migrate |
| `blueprints/` | `auth`, `servers` (HTML), `api` (JSON metrics) |
| `schemas/` | Marshmallow (no SSH secrets in dumps) |
| `metrics/` | Local psutil + remote SSH collectors |
| `migrations/` | Flask-Migrate / Alembic |
| `templates/` · `static/` | UI + ~10s refresh JS |
| `deploy/k8s/` | Optional Kubernetes manifests |
| `Dockerfile` | Optional container image |

## Security (demo)

- Default bind **127.0.0.1**; use `BIND_HOST=0.0.0.0` only in containers/k8s
- Admin password **hashed** (Werkzeug); session cookie HttpOnly
- SSH secrets never echoed in HTML/JSON
- Remote metrics use **fixed** shell commands only
- SSH host keys: `RejectPolicy` + `~/.ssh/known_hosts` by default; opt-in `SSH_AUTO_ADD_HOST_KEYS=1` for demo only — see [docs/metrics.md](docs/metrics.md)
- `FLASK_ENV=production` refuses weak/default `FLASK_SECRET_KEY` / `ADMIN_PASSWORD`

## Docs

| Doc | Topic |
|-----|--------|
| [architecture.md](docs/architecture.md) | Factory, blueprints, full route map |
| [deploy.md](docs/deploy.md) | Optional Docker / Kubernetes |
| [requirements.md](docs/requirements.md) | PRD / acceptance |
| [TODO.md](docs/TODO.md) | Phased checklist |
| [ui.md](docs/ui.md) | Pages and refresh |
| [auth.md](docs/auth.md) | Sign-in |
| [servers.md](docs/servers.md) | Inventory CRUD |
| [metrics.md](docs/metrics.md) | Collection + API shapes |
| [ci.md](docs/ci.md) | GitHub Actions |

## Cursor

- Rules: [`.cursor/rules/`](.cursor/rules/)
- Skill: [`.agents/skills/flask-python/`](.agents/skills/flask-python/)
- Slash command: **`/documentation`** → [`.cursor/commands/documentation.md`](.cursor/commands/documentation.md)

In the Agent chat input, type `/` and choose **documentation** (or type `/documentation`) to re-sync docs with the codebase.
