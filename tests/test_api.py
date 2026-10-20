import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    return app.test_client()


def make(client, **fields):
    body = {"title": "Cannot log in", **fields}
    return client.post("/tickets", json=body)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_ticket(client):
    res = make(client, priority="high")
    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == "open" and body["priority"] == "high" and body["id"] == 1


def test_create_rejects_missing_title(client):
    res = client.post("/tickets", json={"description": "no title"})
    assert res.status_code == 400
    assert "title" in res.get_json()["error"]


def test_create_rejects_non_json(client):
    assert client.post("/tickets", data="plain text").status_code == 400


def test_get_ticket_and_404(client):
    make(client)
    assert client.get("/tickets/1").status_code == 200
    assert client.get("/tickets/99").status_code == 404


def test_list_and_filter(client):
    make(client, priority="low")
    make(client, priority="urgent")
    assert len(client.get("/tickets").get_json()) == 2
    urgent = client.get("/tickets?priority=urgent").get_json()
    assert len(urgent) == 1 and urgent[0]["priority"] == "urgent"
    assert client.get("/tickets?status=nonsense").status_code == 400


def test_valid_status_flow(client):
    make(client)
    for new in ("in_progress", "resolved", "closed"):
        res = client.patch("/tickets/1", json={"status": new})
        assert res.status_code == 200 and res.get_json()["status"] == new


def test_invalid_transition_conflicts(client):
    make(client)
    res = client.patch("/tickets/1", json={"status": "resolved"})
    assert res.status_code == 409


def test_closed_ticket_cannot_reopen(client):
    make(client)
    client.patch("/tickets/1", json={"status": "closed"})
    assert client.patch("/tickets/1", json={"status": "open"}).status_code == 409


def test_patch_priority_and_validation(client):
    make(client)
    assert client.patch("/tickets/1", json={"priority": "urgent"}).get_json()["priority"] == "urgent"
    assert client.patch("/tickets/1", json={"priority": "bad"}).status_code == 400
    assert client.patch("/tickets/1", json={}).status_code == 400
    assert client.patch("/tickets/99", json={"priority": "low"}).status_code == 404


def test_stats(client):
    make(client)
    make(client)
    client.patch("/tickets/1", json={"status": "in_progress"})
    stats = client.get("/stats").get_json()
    assert stats == {"open": 1, "in_progress": 1, "resolved": 0, "closed": 0, "total": 2}


def test_sql_injection_attempt_is_stored_as_plain_text(client):
    nasty = "x'); DROP TABLE tickets;--"
    assert make(client, title=nasty).status_code == 201
    assert client.get("/tickets/1").get_json()["title"] == nasty
    assert client.get("/stats").get_json()["total"] == 1
