"""Localhost metrics via psutil (read-only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psutil


def collect_local_metrics(*, server_id: int | None = None) -> dict[str, Any]:
    """CPU, memory, network I/O, and listening ports for this machine."""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    ports = _listening_ports()

    return {
        "server_id": server_id,
        "status": "ok",
        "error": None,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": round(float(cpu), 1),
        "memory": {
            "used_bytes": int(mem.used),
            "total_bytes": int(mem.total),
            "percent": round(float(mem.percent), 1),
        },
        "network": {
            "bytes_sent": int(net.bytes_sent),
            "bytes_recv": int(net.bytes_recv),
        },
        "listening_ports": ports,
    }


def _listening_ports(limit: int = 80) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, str]] = set()
    rows: list[dict[str, Any]] = []
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        return rows

    for conn in connections:
        if conn.status != psutil.CONN_LISTEN:
            continue
        if not conn.laddr:
            continue
        addr = conn.laddr.ip
        port = int(conn.laddr.port)
        proto = "tcp" if conn.type == 1 else "udp"  # socket.SOCK_STREAM == 1
        key = (proto, port, addr)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"proto": proto, "port": port, "address": addr})
        if len(rows) >= limit:
            break

    rows.sort(key=lambda r: (r["port"], r["proto"], r["address"]))
    return rows
