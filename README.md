# DemoMonitor

Local Flask + SQLite demo for read-only Linux server metrics (CPU, memory, network, ports).

## Run

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set FLASK_SECRET_KEY / ADMIN_PASSWORD
python app.py          # http://127.0.0.1:5000  (admin / ADMIN_PASSWORD)
pytest
```

## Docs

- [requirements.md](docs/requirements.md) — PRD
- [TODO.md](docs/TODO.md) — phased checklist
- [auth.md](docs/auth.md) · [servers.md](docs/servers.md) · [metrics.md](docs/metrics.md) · [ci.md](docs/ci.md)

## Cursor rules

Project agent rules live in [`.cursor/rules/`](.cursor/rules/) (`alwaysApply`).
