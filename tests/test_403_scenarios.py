from __future__ import annotations


def test_real_header_bypass_scenarios(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json() == {"status": "ok", "service": "renikApp"}
    assert client.get("/403/secret").status_code == 403
    assert client.get("/403/secret", headers={"X-Forwarded-For": "127.0.0.1"}).status_code == 200
    assert client.get(
        "/403/original-url-only",
        headers={"X-Original-URL": "/403/original-url-only"},
    ).status_code == 200
    assert client.get(
        "/403/method-override-only",
        headers={"X-HTTP-Method-Override": "GET"},
    ).status_code == 200
    assert client.get(
        "/403/header-combo-only",
        headers={
            "X-Forwarded-For": "127.0.0.1",
            "X-Original-URL": "/403/header-combo-only",
        },
    ).status_code == 200


def test_false_positive_scenarios_are_deterministic_enough_for_scoring(client):
    assert client.get("/403/fake-200").status_code == 200
    assert client.get("/403/fake-302", follow_redirects=False).status_code == 302
    first = client.get("/403/dynamic-forbidden")
    second = client.get("/403/dynamic-forbidden")
    assert first.status_code == second.status_code == 403
    assert first.data != second.data

    same_length = client.get("/403/same-length-different-body")
    assert same_length.status_code == 200
    assert len(same_length.data) == 54

    fake_json = client.get("/403/fake-json-200")
    assert fake_json.status_code == 200
    assert fake_json.get_json()["code"] == 403
