# Architecture

DemoMonitor is a local Flask + SQLite demo structured with an application factory and blueprints (see `.agents/skills/flask-python`).

## Layout

| Piece | Location |
|-------|----------|
| Factory / entry | `app.py` (`create_app`) |
| Config objects | `config.py` (`Development` / `Testing` / `Production`) |
| Extensions | `extensions.py` (`db`, `migrate`) |
| Models | `models.py` (`User`, `Server`) |
| Blueprints | `blueprints/auth.py`, `servers.py`, `api.py` |
| Marshmallow schemas | `schemas/` |
| Auth helpers | `utils/auth.py` (session cookie — **not JWT**) |
| Server form helpers | `utils/servers.py` |
| Errors | `errors.py` |
| Metrics collectors | `metrics/` (`local.py`, `ssh.py`) |
| Templates / static | `templates/`, `static/css/`, `static/js/metrics.js` |
| Tests | `tests/test_auth.py`, `test_servers.py`, `test_metrics.py` |
| Migrations | `migrations/` |
| Container / k8s (optional) | `Dockerfile`, `deploy/k8s/` |

## Routes

### HTML (`auth`, `servers`)

| Method | Path | Endpoint | Auth |
|--------|------|----------|------|
| GET, POST | `/login` | `auth.login` | public |
| GET, POST | `/logout` | `auth.logout` | public |
| GET | `/` | `servers.home` | session |
| GET, POST | `/servers/new` | `servers.server_new` | session |
| GET, POST | `/servers/<id>/edit` | `servers.server_edit` | session |
| POST | `/servers/<id>/delete` | `servers.server_delete` | session |
| GET | `/servers/<id>` | `servers.server_detail` | session |

### JSON API (`api` blueprint, Flask-RESTful)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/api/servers/metrics` | Batch metrics for dashboard cards | session |
| GET | `/api/servers/<id>/metrics` | One server’s metrics | session |

Payloads use Marshmallow (`schemas/metrics.py`, `schemas/server.py`). **Never** include `ssh_password` or key material.

## Request flow

1. Browser hits HTML routes or JSON under `/api/...`
2. `login_required` enforces a session for protected views and API resources
3. Metrics API calls `metrics.collect_for_server` → psutil (local) or Paramiko (remote)
4. Marshmallow dumps safe payloads

## Auth

The flask-python skill suggests JWT. This demo keeps **HttpOnly session cookies** (`SESSION_COOKIE_HTTPONLY`, `SameSite=Lax`) for the HTML UI per the PRD. Metrics APIs share that session.

## Config / env

| Variable | Role | Default |
|----------|------|---------|
| `FLASK_SECRET_KEY` | Session signing | `demo-dev-secret` |
| `ADMIN_PASSWORD` | Seeded admin password (hashed at rest) | `admin123` |
| `FLASK_ENV` | Config object (`development` / `testing` / `production`) | `development` |
| `BIND_HOST` | Listen address | `127.0.0.1` |
| `BIND_PORT` | Listen port | `5000` |

Copy `.env.example` → `.env`. Default bind is **localhost**; use `BIND_HOST=0.0.0.0` only in containers/k8s (see [deploy.md](./deploy.md) and [README.md](../README.md)).

## Migrations

```bash
export FLASK_APP=app.py
flask db migrate -m "message"
flask db upgrade
```

Startup still calls `db.create_all()` for a zero-friction local first run. Initial revision: `migrations/versions/e9ac3feece81_initial_schema.py`.

## Run & test

See [README.md](../README.md).

```bash
pytest                         # all
pytest tests/test_auth.py
pytest tests/test_servers.py
pytest tests/test_metrics.py
```
