# Auth (Phase 1)

## Sign in

1. Start app: `source venv/bin/activate && python app.py`
2. Open http://127.0.0.1:5000 — unauthenticated users go to `/login`
3. Username: `admin`
4. Password: value of `ADMIN_PASSWORD` (default local demo: `admin123`)

Sign out via the top nav link.

## Security

- Password stored as a **Werkzeug hash** in SQLite (`instance/monitoring.db`) — never plaintext
- Session cookie: `HttpOnly`, `SameSite=Lax`
- Login is POST-only for credentials; failed login shows a generic error (no password echoed)
- Dashboard `/` requires a session

## Config

Copy `.env.example` to `.env`:

```bash
FLASK_SECRET_KEY=change-me-for-local-demo
ADMIN_PASSWORD=admin123
```

## Tests

```bash
source venv/bin/activate
pytest
```

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
