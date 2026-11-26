# PRD: Demo Linux Server Monitoring

## 1. Overview

Local demo app that shows real-time Linux server metrics in a read-only UI so L1/L2/L3 and app teams do not need to SSH in just to check CPU, memory, network, and ports.

**Goal:** Minimal Flask demo, runnable on the same machine as Cursor.

## 2. Users

| Role | Access |
|------|--------|
| Admin (internal) | Sign in, add/edit/remove servers, view all metrics (read-only) |

Single user for this demo: `admin`.

## 3. Problem

Today, checking live memory, CPU, network, and port usage requires logging into each server. This demo centralizes that view in a browser.

## 4. Scope

### In scope

- Attractive, simple Flask UI (read-only metrics)
- Sign-in with username `admin` and a hashed password
- Add / edit / remove Linux servers to monitor
- Live metrics: CPU %, memory used/total, network rx/tx, listening ports
- Auto-refresh every ~10 seconds (plus manual refresh)
- Dashboard of all servers + per-server detail page
- Local deploy only (Flask + SQLite)

### Out of scope

- Windows / non-Linux hosts
- Historical charts, long-term storage, or time-series DB
- Alerts, email, Slack, paging
- Multi-user accounts / RBAC beyond admin
- Docker, cloud deploy, HA
- Agents installed on target hosts (demo uses SSH from the app host)

## 5. Features

### F1 — Read-only monitoring UI

- Clean dashboard listing all monitored servers with status and key metrics
- Server detail page: CPU, memory, network I/O, listening ports
- Metrics are view-only; no remote shell or config changes from the UI
- Auto-refresh ~10s; manual refresh control

### F2 — Admin sign-in

- Default username: `admin`
- Password stored hashed (e.g. Werkzeug / bcrypt); never plaintext
- Unauthenticated users redirected to login
- Simple logout

### F3 — Manage Linux servers

- Add server with: display name, hostname/IP, SSH port (default 22), SSH username, auth (password or path to local private key)
- Edit and delete servers
- Connection/status indicator (reachable / unreachable / error)

## 6. Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3, Flask |
| Frontend | Flask templates + CSS (simple, attractive UI) |
| DB | SQLite |
| Remote metrics | SSH from the app host (e.g. Paramiko) running read-only commands |
| Auth | Session cookie + hashed password |

## 7. Local run (minimal)

1. Create venv and install dependencies from `requirements.txt`
2. Set admin password via env or one-time seed (hashed in DB)
3. Run: `python app.py` (binds `127.0.0.1`)
4. Open `http://127.0.0.1:5000`, sign in as `admin`, add servers

See [README.md](../README.md) and [architecture.md](./architecture.md) for current module layout.  
Optional cluster packaging (not required for the demo acceptance above): [deploy.md](./deploy.md).

## 8. Acceptance criteria (demo)

- [x] Login works only with `admin` + correct password; password is hashed at rest
- [x] Logged-in user can add, edit, and delete Linux server entries
- [x] Dashboard and detail pages show CPU, memory, network, and listening ports
- [x] UI is read-only for metrics; refresh updates values without page redesign
- [x] App runs locally with Flask + SQLite without Docker

## 9. Non-functional (demo-level)

- Single process, local machine only
- Prefer clarity over scale; no production hardening beyond hashed password and basic session auth
- Failures to reach a host show a clear error on that server’s card/page

## 10. Open defaults (assumed)

These were assumed when the PRD was written; change if needed:

- Metrics set: CPU, memory, network I/O, listening ports only
- Collection: SSH agentless from the Cursor/local host
- Refresh: ~10s auto + manual
- Auth: single `admin` user
- No alert thresholds in v1
