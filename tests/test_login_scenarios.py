import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/lp/insecure-login",
        "/lp/secure-login",
        "/lp/default-login",
        "/lp/rate-limit-login",
        "/lp/nosql-login",
        "/lp/username-enum-login",
        "/lp/captcha-login",
        "/lp/xpath-login",
        "/lp/ldap-login",
        "/lp/json-login",
        "/lp/test-account-login",
        "/lp/csrf-login",
        "/lp/graphql-login",
    ],
)
def test_login_scenario_pages_are_available(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert b"<form" in response.data or b"login" in response.data.lower()


def test_insecure_login_accepts_sql_injection(client):
    response = client.post(
        "/lp/insecure-login",
        data={"username": "admin' --", "password": "anything"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/lp/dashboard")


def test_secure_login_rejects_sql_injection(client):
    response = client.post(
        "/lp/secure-login",
        data={"username": "' OR '1'='1", "password": "anything"},
    )

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_default_credentials_scenario(client):
    response = client.post(
        "/lp/default-login", data={"username": "admin", "password": "admin"}
    )

    assert response.status_code == 302
    assert response.headers["Set-Cookie"].startswith("session_id=default_session_")


def test_nosql_operator_bypass_scenario(client):
    response = client.post(
        "/lp/nosql-login",
        json={"username": {"$ne": ""}, "password": {"$ne": ""}},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/lp/dashboard")


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/lp/xpath-login", {"username": "' or true() or '", "password": "x"}),
        ("/lp/ldap-login", {"username": "*", "password": "x"}),
    ],
)
def test_injection_scenarios_accept_documented_payloads(client, path, payload):
    response = client.post(path, data=payload)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/lp/dashboard")


def test_username_enumeration_scenario_exposes_distinct_errors(client):
    unknown = client.post(
        "/lp/username-enum-login",
        data={"username": "does-not-exist", "password": "wrong"},
    )
    known = client.post(
        "/lp/username-enum-login",
        data={"username": "admin", "password": "wrong"},
    )

    assert b"Username not found" in unknown.data
    assert b"Invalid password" in known.data


def test_rate_limit_scenario_returns_429_after_failed_attempts(client):
    payload = {"username": "rate-limit-test-user", "password": "wrong"}

    for _ in range(5):
        response = client.post("/lp/rate-limit-login", data=payload)
        assert response.status_code == 200

    blocked = client.post("/lp/rate-limit-login", data=payload)

    assert blocked.status_code == 429


def test_csrf_scenario_requires_token_but_accepts_non_empty_value(client):
    missing = client.post(
        "/lp/csrf-login",
        data={"username": "admin", "password": "admin"},
    )
    present = client.post(
        "/lp/csrf-login",
        data={"username": "admin", "password": "admin", "csrf_token": "arbitrary"},
    )

    assert b"CSRF token missing" in missing.data
    assert present.status_code == 302


def test_json_and_graphql_login_scenarios(client):
    json_response = client.post(
        "/api/login", json={"username": "admin", "password": "admin"}
    )
    graphql_response = client.post(
        "/api/graphql",
        json={"query": 'mutation { login(username: "admin", password: "admin") { token } }'},
    )

    assert json_response.status_code == 200
    assert json_response.get_json()["status"] == "success"
    assert graphql_response.status_code == 200
    assert graphql_response.get_json()["data"]["login"]["token"]
