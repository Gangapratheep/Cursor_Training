from models import User


def test_password_is_hashed_not_plaintext(app):
    with app.app_context():
        user = User.query.filter_by(username="admin").one()
        assert user.password_hash
        assert user.password_hash != "test-pass-123"
        assert user.check_password("test-pass-123")
        assert not user.check_password("wrong")


def test_protected_home_redirects_when_logged_out(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_rejects_bad_password(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data
    # Still blocked from home
    home = client.get("/", follow_redirects=False)
    assert home.status_code == 302


def test_login_success_and_logout(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    home = client.get("/")
    assert home.status_code == 200
    assert b"Demo" in home.data

    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302
    assert "/login" in logout.headers["Location"]

    blocked = client.get("/", follow_redirects=False)
    assert blocked.status_code == 302
