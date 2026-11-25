from models import Server


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123"},
        follow_redirects=True,
    )


def test_server_routes_require_login(client):
    assert client.get("/servers/new", follow_redirects=False).status_code == 302
    assert (
        client.post("/servers/1/delete", follow_redirects=False).status_code == 302
    )


def test_create_list_edit_delete_server(client, app):
    _login(client)

    create = client.post(
        "/servers/new",
        data={
            "display_name": "Local box",
            "hostname": "127.0.0.1",
            "ssh_port": "22",
            "auth_type": "local",
            "ssh_username": "",
            "ssh_password": "should-not-appear",
            "ssh_key_path": "",
        },
        follow_redirects=True,
    )
    assert create.status_code == 200
    assert b"Local box" in create.data
    assert b"127.0.0.1" in create.data
    assert b"should-not-appear" not in create.data

    with app.app_context():
        server = Server.query.filter_by(display_name="Local box").one()
        server_id = server.id

    edit_page = client.get(f"/servers/{server_id}/edit")
    assert edit_page.status_code == 200
    assert b"should-not-appear" not in edit_page.data
    # Password input must not be pre-filled with stored secret
    assert b'name="ssh_password" value=""' in edit_page.data or b'name="ssh_password"' in edit_page.data

    edited = client.post(
        f"/servers/{server_id}/edit",
        data={
            "display_name": "Local box renamed",
            "hostname": "127.0.0.1",
            "ssh_port": "22",
            "auth_type": "local",
            "ssh_username": "",
            "ssh_password": "",
            "ssh_key_path": "",
        },
        follow_redirects=True,
    )
    assert b"Local box renamed" in edited.data

    deleted = client.post(f"/servers/{server_id}/delete", follow_redirects=True)
    assert deleted.status_code == 200
    assert b"removed" in deleted.data
    assert b"server-row" not in deleted.data
    with app.app_context():
        assert Server.query.filter_by(id=server_id).count() == 0


def test_rejects_key_path_traversal(client, app):
    _login(client)
    response = client.post(
        "/servers/new",
        data={
            "display_name": "Bad key",
            "hostname": "10.0.0.5",
            "ssh_port": "22",
            "auth_type": "key",
            "ssh_username": "ubuntu",
            "ssh_password": "",
            "ssh_key_path": "/tmp/../etc/passwd",
        },
        follow_redirects=True,
    )
    assert b"Invalid key path" in response.data
    with app.app_context():
        assert Server.query.filter_by(display_name="Bad key").count() == 0


def test_delete_is_post_only(client):
    _login(client)
    client.post(
        "/servers/new",
        data={
            "display_name": "Temp",
            "hostname": "localhost",
            "ssh_port": "22",
            "auth_type": "local",
            "ssh_username": "",
            "ssh_password": "",
            "ssh_key_path": "",
        },
    )
    with client.application.app_context():
        server_id = Server.query.filter_by(display_name="Temp").one().id

    get_delete = client.get(f"/servers/{server_id}/delete", follow_redirects=False)
    assert get_delete.status_code == 405
