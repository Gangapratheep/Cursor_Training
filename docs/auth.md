# Auth

Session-cookie sign-in for the single demo user `admin`.

## Sign in

1. `source venv/bin/activate && python app.py`
2. Open http://127.0.0.1:5000 — unauthenticated users go to `/login`
3. Username: `admin`
4. Password: `ADMIN_PASSWORD` (default local demo: `admin123`)

Sign out via the top nav (**Sign out** → `/logout`, GET or POST).

## Security

- Password stored as a **Werkzeug hash** in SQLite — never plaintext
- Session cookie: `HttpOnly`, `SameSite=Lax`
- Login credentials accepted on **POST** only; failed login shows a generic error (no password echoed)
- HTML pages and `/api/*` require a session (`utils/auth.py` → `login_required`)
- Not JWT — session auth matches the PRD HTML demo (see [architecture.md](./architecture.md))

## Config

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `FLASK_SECRET_KEY` | Session signing |
| `ADMIN_PASSWORD` | Seeded `admin` password |
| `FLASK_ENV` | Optional; default `development` |
| `BIND_HOST` | Listen address (default `127.0.0.1`; `0.0.0.0` for k8s) |
| `BIND_PORT` | Listen port (default `5000`) |

## Code

- Blueprint: `blueprints/auth.py`
- Model: `models.User`
- Seeded on startup in `app.create_app`

## Tests

```bash
pytest tests/test_auth.py
```
