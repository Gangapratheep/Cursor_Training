# TODO: Demo Linux Server Monitoring

Incremental checklist for AI-assisted development. Keep each step small and shippable. Demo runs **locally** (Flask + SQLite) on the Cursor host — no Docker/cloud.

Reference: [requirements.md](./requirements.md)

---

## Phase 0 — Project init + basic UI

Layout matches PRD §6 (`app.py`, `templates/`, `static/`, Flask). See [ui.md](./ui.md).

- [x] **0.1** Create project layout (`app.py` or `app/`, `templates/`, `static/`, `tests/`, `docs/`, `.gitignore`)
  - Security: ignore `.env`, `*.db`, `venv/`, secrets; never commit credentials
  - Docs: one-line note in this file that layout matches PRD §6
- [x] **0.2** Add `requirements.txt` (Flask only for now) + create venv and install
  - Security: pin major versions; no unused packages
  - Docs: minimal run note — `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- [x] **0.3** Hello Flask app that serves a static/basic home page (brand + placeholder dashboard shell)
  - Security: bind `127.0.0.1` only; set `SECRET_KEY` from env (placeholder OK)
  - Docs: “Open http://127.0.0.1:5000”
- [x] **0.4** Add base template + CSS (read-only look; nav placeholders; no real data yet)
  - Security: no inline user-controlled HTML; use Jinja auto-escaping (default on)
  - Docs: screenshot or short UI note under `docs/` if helpful (optional for demo)

---

## Phase 1 — Sign-in + unit tests

See [auth.md](./auth.md). CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

- [x] **1.1** Add SQLite + user model with **hashed** password (`werkzeug.security`)
  - Security: never store plaintext passwords; seed `admin` only via env `ADMIN_PASSWORD` (default for local demo only)
  - Docs: document default username `admin` and env var in `docs/requirements.md` §7 or a short `docs/auth.md`
- [x] **1.2** Login page + session cookie auth + logout; protect `/` behind login
  - Security: `HttpOnly` session cookie; POST-only login; redirect unauthenticated users; no password in logs/flash
  - Docs: login steps (username/password) in auth doc
- [x] **1.3** Unit tests for hash verify, bad login, good login, logout, protected route redirect
  - Security: tests must assert failure cases (wrong password, no session)
  - Docs: how to run tests — `pytest` (add `pytest` to requirements when introduced)
- [x] **1.4** Wire CI early: GitHub Actions workflow that installs deps and runs tests on push/PR
  - Security: no secrets in workflow logs; use dummy `SECRET_KEY` / `ADMIN_PASSWORD` in CI env only
  - Docs: link workflow path in this TODO (e.g. `.github/workflows/ci.yml`)

---

## Phase 2 — Server inventory (CRUD)

See [servers.md](./servers.md). CI still runs full `pytest` (same workflow).

- [x] **2.1** `Server` model (display name, hostname/IP, SSH port, username, auth type, password/key path)
  - Security: mark SSH password field as sensitive; plan not to echo it in HTML value attrs on edit (blank = keep existing)
  - Docs: field list in a short `docs/servers.md`
- [x] **2.2** Add-server form + create route (validated required fields)
  - Security: CSRF later if time; for demo at least require login + validate/sanitize inputs; reject path traversal on key paths where practical
  - Docs: how to add a server (local vs SSH)
- [x] **2.3** List servers on dashboard (names/hosts only — no metrics yet)
  - Security: authorize all routes with login; do not expose SSH passwords in list/JSON
  - Docs: update UI note
- [x] **2.4** Edit + delete server (POST for delete)
  - Security: POST-only delete; confirm in UI; no mass assignment of unexpected fields
  - Docs: edit/delete steps
- [x] **2.5** Unit tests for create/edit/delete and “password not returned in page/API”
  - Security: assert secrets absent from responses
  - Docs: mention tests in `docs/servers.md`
- [x] **2.6** Extend CI to run new tests (same workflow)

---

## Phase 3 — Local metrics (read-only)

- [ ] **3.1** Add `psutil`; collect CPU %, memory used/total for **localhost** only
  - Security: read-only APIs; no shell mutation commands
  - Docs: `docs/metrics.md` — local collection
- [ ] **3.2** JSON endpoint for one server’s metrics (login-required) + show on detail page
  - Security: login required; no eval of remote input; rate-limit not required for demo
  - Docs: endpoint path and sample fields
- [ ] **3.3** Network rx/tx + listening ports for local host
  - Security: display only; do not offer kill-process or firewall actions
  - Docs: update metrics field list
- [ ] **3.4** Unit tests with mocked `psutil` (no flaky live system asserts)
  - Security: tests don’t need real host privileges
  - Docs: how metrics tests are mocked
- [ ] **3.5** CI still green

---

## Phase 4 — SSH metrics (remote Linux)

- [ ] **4.1** Add Paramiko; SSH connect helper with timeout; support password **or** key path
  - Security: connect timeout; fail closed; AutoAddPolicy OK for **demo only** — document host-key risk; never log passwords/keys
  - Docs: SSH auth options + demo host-key warning in `docs/metrics.md`
- [ ] **4.2** Remote read-only commands for CPU/mem (`/proc` preferred)
  - Security: fixed command strings only (no user-supplied shell); read `/proc` only
  - Docs: commands used (inventory for review)
- [ ] **4.3** Remote network + listening ports (`ss`/`netstat` parse)
  - Security: same fixed commands; parse safely
  - Docs: update command list
- [ ] **4.4** Status indicator: reachable / unreachable / error message on UI
  - Security: sanitize/truncate error messages so they don’t leak local paths unnecessarily
  - Docs: status meanings
- [ ] **4.5** Unit tests with mocked SSH client (success + auth failure + timeout)
  - Security: no real SSH to external hosts in CI
  - Docs: note mocks in metrics doc
- [ ] **4.6** CI green (Paramiko installed in workflow)

---

## Phase 5 — Dashboard UX polish

- [ ] **5.1** Dashboard cards with live summary metrics via one batch JSON API
  - Security: login-required API; no secrets in payload
  - Docs: API shape
- [ ] **5.2** Auto-refresh ~10s + manual refresh control
  - Security: refresh only hits our APIs; no third-party script CDNs unless needed (prefer local static)
  - Docs: refresh behavior
- [ ] **5.3** Empty state + friendly errors when no servers / unreachable
  - Security: user-safe error copy
  - Docs: optional
- [ ] **5.4** Light UI polish (CSS only) — keep read-only feel
  - Security: no XSS via unescaped metric strings (Jinja escaping)
  - Docs: none required beyond PRD F1

---

## Phase 6 — CI/CD (GitHub Actions) + final docs

- [ ] **6.1** Finalize `.github/workflows/ci.yml`: lint optional, **pytest required**, cache pip
  - Security: `permissions: contents: read`; no deploy keys; env secrets only for CI dummies
  - Docs: “CI” section in `docs/TODO.md` or short `docs/ci.md`
- [ ] **6.2** Add workflow_dispatch for manual CI runs (optional)
  - Security: same as above
  - Docs: how to re-run checks
- [ ] **6.3** Acceptance pass against PRD §8 checklist; tick boxes in `docs/requirements.md`
  - Security: confirm hashed password, localhost bind, no plaintext secrets in repo
  - Docs: mark demo “done locally” with 3-line run instructions only

---

## Local run (minimal)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set FLASK_SECRET_KEY / ADMIN_PASSWORD
python app.py          # http://127.0.0.1:5000  (admin / ADMIN_PASSWORD)
pytest
```

---

## Progress legend

| Status | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[x]` | Done |

Work **one checkbox at a time**. Do not skip security or docs bullets inside a step.
