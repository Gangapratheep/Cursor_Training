"""Remote Linux metrics over SSH (Paramiko)."""

from __future__ import annotations

import os
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import paramiko

from metrics.common import sanitize_error

# Fixed read-only commands — never interpolate user input into the shell.
CMD_MEMINFO = "cat /proc/meminfo"
CMD_STAT = "cat /proc/stat"
CMD_NET_DEV = "cat /proc/net/dev"
CMD_SS = "ss -lntuH"

SSH_CONNECT_TIMEOUT = 8
SSH_CMD_TIMEOUT = 10


def _host_key_policy() -> paramiko.MissingHostKeyPolicy:
    """
    Default: RejectPolicy (unknown hosts fail closed).
    Opt-in demo MITM-prone mode: SSH_AUTO_ADD_HOST_KEYS=1|true|yes
    """
    flag = (os.environ.get("SSH_AUTO_ADD_HOST_KEYS") or "").strip().lower()
    if flag in {"1", "true", "yes"}:
        return paramiko.AutoAddPolicy()
    return paramiko.RejectPolicy()


def connect_ssh(
    *,
    hostname: str,
    port: int,
    username: str,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
) -> paramiko.SSHClient:
    """Open an SSH session with known_hosts loaded when present."""
    client = paramiko.SSHClient()
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    if known_hosts.is_file():
        client.load_host_keys(str(known_hosts))
    client.set_missing_host_key_policy(_host_key_policy())
    connect_kwargs: dict[str, Any] = {
        "hostname": hostname,
        "port": port,
        "username": username,
        "timeout": SSH_CONNECT_TIMEOUT,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if key_path:
        connect_kwargs["key_filename"] = key_path
        if password:
            connect_kwargs["passphrase"] = password
    else:
        connect_kwargs["password"] = password or ""

    try:
        client.connect(**connect_kwargs)
    except Exception:
        client.close()
        raise
    return client


def _run(client: paramiko.SSHClient, command: str) -> str:
    _stdin, stdout, stderr = client.exec_command(command, timeout=SSH_CMD_TIMEOUT)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0 and not out.strip():
        raise RuntimeError(err.strip() or f"Command failed ({exit_status})")
    return out


def _parse_meminfo(text: str) -> dict[str, Any]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if not parts:
            continue
        try:
            # /proc/meminfo values are in kB
            values[key] = int(parts[0]) * 1024
        except ValueError:
            continue
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = max(total - available, 0)
    percent = round((used / total) * 100, 1) if total else 0.0
    return {"used_bytes": used, "total_bytes": total, "percent": percent}


def _cpu_percent_from_stat(first: str, second: str) -> float:
    def idle_total(blob: str) -> tuple[int, int]:
        for line in blob.splitlines():
            if line.startswith("cpu "):
                fields = [int(x) for x in line.split()[1:]]
                idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
                return idle, sum(fields)
        return 0, 0

    idle1, total1 = idle_total(first)
    idle2, total2 = idle_total(second)
    d_total = total2 - total1
    d_idle = idle2 - idle1
    if d_total <= 0:
        return 0.0
    return round(max(0.0, min(100.0, (1 - d_idle / d_total) * 100)), 1)


def _parse_net_dev(text: str) -> dict[str, int]:
    recv_total = 0
    sent_total = 0
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        iface = name.strip()
        if iface == "lo":
            continue
        cols = rest.split()
        if len(cols) < 9:
            continue
        try:
            recv_total += int(cols[0])
            sent_total += int(cols[8])
        except ValueError:
            continue
    return {"bytes_recv": recv_total, "bytes_sent": sent_total}


# ss -lntuH: Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port
_SS_RE = re.compile(
    r"^(?P<proto>tcp|udp)\s+\S+\s+\S+\s+\S+\s+(?P<local>\S+)",
    re.IGNORECASE,
)


def _parse_ss(text: str, limit: int = 80) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for line in text.splitlines():
        match = _SS_RE.match(line.strip())
        if not match:
            continue
        proto = match.group("proto").lower()
        local = match.group("local")
        # Formats: 0.0.0.0:22  [::]:80  *:443  127.0.0.1:5432
        if local.startswith("["):
            # [addr]:port
            end = local.rfind("]:")
            if end == -1:
                continue
            addr = local[1:end]
            try:
                port = int(local[end + 2 :])
            except ValueError:
                continue
        else:
            if ":" not in local:
                continue
            addr, port_s = local.rsplit(":", 1)
            try:
                port = int(port_s)
            except ValueError:
                continue
            if addr == "*":
                addr = "0.0.0.0"
        key = (proto, port, addr)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"proto": proto, "port": port, "address": addr})
        if len(rows) >= limit:
            break
    rows.sort(key=lambda r: (r["port"], r["proto"], r["address"]))
    return rows


def collect_remote_metrics(server) -> dict[str, Any]:
    """Fetch metrics from a remote Linux host over SSH."""
    client: Optional[paramiko.SSHClient] = None
    try:
        client = connect_ssh(
            hostname=server.hostname,
            port=int(server.ssh_port or 22),
            username=server.ssh_username,
            password=server.ssh_password,
            key_path=server.ssh_key_path if server.auth_type == "key" else None,
        )
        stat1 = _run(client, CMD_STAT)
        time.sleep(0.15)
        stat2 = _run(client, CMD_STAT)
        meminfo = _run(client, CMD_MEMINFO)
        net_dev = _run(client, CMD_NET_DEV)
        try:
            ss_out = _run(client, CMD_SS)
        except RuntimeError:
            ss_out = ""

        return {
            "server_id": server.id,
            "status": "ok",
            "error": None,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": _cpu_percent_from_stat(stat1, stat2),
            "memory": _parse_meminfo(meminfo),
            "network": _parse_net_dev(net_dev),
            "listening_ports": _parse_ss(ss_out),
        }
    except (socket.timeout, TimeoutError, paramiko.SSHException, OSError) as exc:
        status = "unreachable"
        if isinstance(exc, paramiko.AuthenticationException):
            status = "error"
        return {
            "server_id": server.id,
            "status": status,
            "error": sanitize_error(str(exc) or type(exc).__name__),
            "collected_at": None,
            "cpu_percent": None,
            "memory": None,
            "network": None,
            "listening_ports": [],
        }
    finally:
        if client is not None:
            client.close()
