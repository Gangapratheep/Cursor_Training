"""Read-only metrics collection for local (psutil) and remote (SSH) Linux hosts."""

from __future__ import annotations

from typing import Any

from metrics.common import sanitize_error
from metrics.local import collect_local_metrics
from metrics.ssh import collect_remote_metrics

__all__ = ["collect_for_server", "sanitize_error"]


def collect_for_server(server) -> dict[str, Any]:
    """Collect metrics for a Server model instance. Never includes secrets."""
    try:
        if server.is_local():
            return collect_local_metrics(server_id=server.id)
        return collect_remote_metrics(server)
    except Exception as exc:  # noqa: BLE001 — surface as status for UI
        return {
            "server_id": server.id,
            "status": "error",
            "error": sanitize_error(str(exc)),
            "collected_at": None,
            "cpu_percent": None,
            "memory": None,
            "network": None,
            "listening_ports": [],
        }
