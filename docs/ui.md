# UI

Brand **DemoMonitor** — read-only monitoring shell (Flask templates + CSS + local JS).

## Pages

| Page | Route | Blueprint endpoint |
|------|-------|--------------------|
| Sign in | `/login` | `auth.login` |
| Dashboard | `/` | `servers.home` |
| Add server | `/servers/new` | `servers.server_new` |
| Edit server | `/servers/<id>/edit` | `servers.server_edit` |
| Server detail | `/servers/<id>` | `servers.server_detail` |
| Sign out | `/logout` | `auth.logout` |

## Behavior

- Dashboard cards: CPU %, memory %, net rx/tx, status pill
- Detail page: CPU, memory used/total, network rx·tx, listening ports table
- Auto-refresh ~**10s** (`static/js/metrics.js`) + **Refresh now**
- Empty state when no servers are registered
- Status pills: `ok` / `unreachable` / `error` / `loading`
- Jinja auto-escaping on; JS sets values with `textContent` (no HTML injection)
- Refresh calls only same-origin `/api/servers/...` endpoints

## Open

`http://127.0.0.1:5000` (default; app binds localhost only)
