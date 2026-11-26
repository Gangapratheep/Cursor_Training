from unittest.mock import MagicMock, patch

from models import Server


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123"},
        follow_redirects=True,
    )


def _add_local_server(client, name="Local"):
    return client.post(
        "/servers/new",
        data={
            "display_name": name,
            "hostname": "127.0.0.1",
            "ssh_port": "22",
            "auth_type": "local",
            "ssh_username": "",
            "ssh_password": "secret-should-never-appear",
            "ssh_key_path": "",
        },
        follow_redirects=True,
    )


def _add_remote_server(client, name="Remote"):
    return client.post(
        "/servers/new",
        data={
            "display_name": name,
            "hostname": "10.0.0.9",
            "ssh_port": "22",
            "auth_type": "password",
            "ssh_username": "ubuntu",
            "ssh_password": "ssh-secret",
            "ssh_key_path": "",
        },
        follow_redirects=True,
    )


def test_metrics_api_requires_login(client):
    assert client.get("/api/servers/1/metrics", follow_redirects=False).status_code == 302
    assert client.get("/api/servers/metrics", follow_redirects=False).status_code == 302


@patch("metrics.local.psutil")
def test_local_metrics_json(mock_psutil, client, app):
    mock_psutil.cpu_percent.return_value = 12.3
    mem = MagicMock(used=1000, total=4000, percent=25.0)
    mock_psutil.virtual_memory.return_value = mem
    mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=50, bytes_recv=80)
    mock_psutil.CONN_LISTEN = "LISTEN"
    mock_psutil.AccessDenied = type("AccessDenied", (Exception,), {})
    conn = MagicMock()
    conn.status = "LISTEN"
    conn.type = 1
    conn.laddr = MagicMock(ip="0.0.0.0", port=22)
    mock_psutil.net_connections.return_value = [conn]

    _login(client)
    _add_local_server(client)
    with app.app_context():
        server_id = Server.query.filter_by(display_name="Local").one().id

    response = client.get(f"/api/servers/{server_id}/metrics")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["cpu_percent"] == 12.3
    assert data["memory"]["percent"] == 25.0
    assert data["network"]["bytes_recv"] == 80
    assert any(p["port"] == 22 for p in data["listening_ports"])
    assert b"secret-should-never-appear" not in response.data


@patch("app.collect_for_server")
def test_batch_metrics_and_detail_page(mock_collect, client, app):
    mock_collect.return_value = {
        "server_id": 1,
        "status": "ok",
        "error": None,
        "collected_at": "2026-01-01T00:00:00+00:00",
        "cpu_percent": 5.0,
        "memory": {"used_bytes": 1, "total_bytes": 2, "percent": 50.0},
        "network": {"bytes_sent": 3, "bytes_recv": 4},
        "listening_ports": [],
    }
    _login(client)
    _add_local_server(client, name="BatchHost")
    with app.app_context():
        server_id = Server.query.filter_by(display_name="BatchHost").one().id

    batch = client.get("/api/servers/metrics")
    assert batch.status_code == 200
    payload = batch.get_json()
    assert len(payload["servers"]) == 1
    assert payload["servers"][0]["display_name"] == "BatchHost"
    assert "ssh_password" not in payload["servers"][0]
    assert payload["servers"][0]["metrics"]["cpu_percent"] == 5.0

    detail = client.get(f"/servers/{server_id}")
    assert detail.status_code == 200
    assert b"BatchHost" in detail.data
    assert b"secret-should-never-appear" not in detail.data


@patch("metrics.ssh.connect_ssh")
def test_remote_metrics_success(mock_connect, client, app):
    client_mock = MagicMock()

    def exec_command(cmd, timeout=10):
        stdout = MagicMock()
        stderr = MagicMock()
        stderr.read.return_value = b""
        stdout.channel.recv_exit_status.return_value = 0
        if "meminfo" in cmd:
            stdout.read.return_value = (
                b"MemTotal:        2000000 kB\nMemAvailable:    1000000 kB\n"
            )
        elif "stat" in cmd:
            # two samples differ slightly via side_effect below
            stdout.read.return_value = b"cpu  100 0 0 900 0 0 0 0\n"
        elif "net/dev" in cmd:
            stdout.read.return_value = (
                b"Inter-|   Receive                                                |  Transmit\n"
                b" eth0: 1000 0 0 0 0 0 0 0 2000 0 0 0 0 0 0 0\n"
            )
        elif cmd.startswith("ss "):
            stdout.read.return_value = b"tcp   LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
        else:
            stdout.read.return_value = b""
        return MagicMock(), stdout, stderr

    # Vary /proc/stat across calls for CPU delta
    calls = {"n": 0}

    def exec_with_cpu(cmd, timeout=10):
        _stdin, stdout, stderr = exec_command(cmd, timeout=timeout)
        if "stat" in cmd:
            calls["n"] += 1
            if calls["n"] == 1:
                stdout.read.return_value = b"cpu  100 0 0 900 0 0 0 0\n"
            else:
                stdout.read.return_value = b"cpu  200 0 0 1000 0 0 0 0\n"
        return _stdin, stdout, stderr

    client_mock.exec_command.side_effect = exec_with_cpu
    mock_connect.return_value = client_mock

    _login(client)
    _add_remote_server(client)
    with app.app_context():
        server_id = Server.query.filter_by(display_name="Remote").one().id

    with patch("metrics.ssh.time.sleep", return_value=None):
        response = client.get(f"/api/servers/{server_id}/metrics")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["memory"]["total_bytes"] == 2000000 * 1024
    assert data["network"]["bytes_recv"] == 1000
    assert any(p["port"] == 22 for p in data["listening_ports"])
    assert b"ssh-secret" not in response.data
    mock_connect.assert_called_once()
    client_mock.close.assert_called()


@patch("metrics.ssh.connect_ssh")
def test_remote_auth_failure(mock_connect, client, app):
    import paramiko

    mock_connect.side_effect = paramiko.AuthenticationException("Authentication failed.")
    _login(client)
    _add_remote_server(client, name="BadAuth")
    with app.app_context():
        server_id = Server.query.filter_by(display_name="BadAuth").one().id

    response = client.get(f"/api/servers/{server_id}/metrics")
    data = response.get_json()
    assert data["status"] == "error"
    assert data["cpu_percent"] is None
    assert "Authentication" in (data["error"] or "")


@patch("metrics.ssh.connect_ssh")
def test_remote_timeout_unreachable(mock_connect, client, app):
    mock_connect.side_effect = TimeoutError("timed out")
    _login(client)
    _add_remote_server(client, name="SlowHost")
    with app.app_context():
        server_id = Server.query.filter_by(display_name="SlowHost").one().id

    response = client.get(f"/api/servers/{server_id}/metrics")
    data = response.get_json()
    assert data["status"] == "unreachable"
    assert data["listening_ports"] == []


def test_sanitize_error_redacts_paths():
    from metrics.common import sanitize_error

    msg = sanitize_error("failed reading /home/jumpuser19/.ssh/id_rsa detail")
    assert "/home/" not in msg
    assert "[path]" in msg
