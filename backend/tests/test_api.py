"""API-level tests: auth, CRUD, execution persistence, authorization and
webhook isolation between users."""


def _demo_nodes():
    return [
        {"id": "n1", "type": "manual_trigger", "name": "Start", "position": {"x": 0, "y": 0}, "config": {}},
        {
            "id": "n2",
            "type": "transform",
            "name": "Enrich",
            "position": {"x": 150, "y": 0},
            "config": {"expression": '{"greeting": "hello " + input.name}'},
        },
        {
            "id": "n3",
            "type": "log",
            "name": "Log",
            "position": {"x": 300, "y": 0},
            "config": {"message": "{{nodes.n2.output.greeting}}"},
        },
    ]


def _demo_edges():
    return [
        {"id": "e1", "source": "n1", "target": "n2"},
        {"id": "e2", "source": "n2", "target": "n3"},
    ]


def test_auth_flow(client):
    email = "new@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret1234"})
    assert r.status_code == 201
    assert r.json()["email"] == email

    r = client.post("/api/auth/login", json={"email": email, "password": "secret1234"})
    assert r.status_code == 200
    assert r.json()["access_token"]

    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_login_wrong_password(client):
    email = "wrongpw@test.com"
    client.post("/api/auth/register", json={"email": email, "password": "secret1234"})
    r = client.post("/api/auth/login", json={"email": email, "password": "nope"})
    assert r.status_code == 401


def test_node_types_endpoint(client, auth_headers):
    r = client.get("/api/workflows/node-types", headers=auth_headers)
    assert r.status_code == 200
    types = {n["type"] for n in r.json()}
    assert {"manual_trigger", "webhook", "transform", "condition", "log", "http_request", "llm"} <= types


def test_workflow_crud_roundtrip(client, auth_headers):
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "Demo", "nodes": _demo_nodes(), "edges": _demo_edges()},
    )
    assert r.status_code == 201, r.text
    wf = r.json()
    assert wf["name"] == "Demo"
    assert len(wf["nodes"]) == 3

    wf_id = wf["id"]

    r = client.get(f"/api/workflows/{wf_id}", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["nodes"]) == 3

    r = client.get("/api/workflows", headers=auth_headers)
    assert any(w["id"] == wf_id for w in r.json())

    r = client.put(f"/api/workflows/{wf_id}", headers=auth_headers, json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    r = client.delete(f"/api/workflows/{wf_id}", headers=auth_headers)
    assert r.status_code == 204


def test_run_workflow_persists_execution(client, auth_headers):
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "RunMe", "nodes": _demo_nodes(), "edges": _demo_edges()},
    )
    wf_id = r.json()["id"]

    r = client.post(
        f"/api/workflows/{wf_id}/run",
        headers=auth_headers,
        json={"input": {"name": "Kanha"}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert body["output"]["logged"] == "hello Kanha"
    assert len(body["nodes"]) == 3
    assert all(n["status"] == "success" for n in body["nodes"])
    assert body["duration_ms"] is not None

    r = client.get(f"/api/workflows/{wf_id}/executions", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    exec_id = body["id"]
    r = client.get(f"/api/executions/{exec_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_execution_persistence_node_history(client, auth_headers):
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "Hist", "nodes": _demo_nodes(), "edges": _demo_edges()},
    )
    wf_id = r.json()["id"]
    r = client.post(f"/api/workflows/{wf_id}/run", headers=auth_headers, json={"input": {"name": "x"}})
    exec_id = r.json()["id"]

    r = client.get(f"/api/executions/{exec_id}", headers=auth_headers)
    nodes = {n["node_id"]: n for n in r.json()["nodes"]}
    assert "n2" in nodes
    assert nodes["n2"]["output"] == {"greeting": "hello x"}
    assert "n3" in nodes


def test_authorization_workflow_isolation(client, auth_headers):
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "Priv", "nodes": _demo_nodes(), "edges": _demo_edges()},
    )
    wf_id = r.json()["id"]

    # Second user
    email = "other@test.com"
    client.post("/api/auth/register", json={"email": email, "password": "password123"})
    r = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.get(f"/api/workflows/{wf_id}", headers=other_headers)
    assert r.status_code in (403, 404)

    r = client.post(f"/api/workflows/{wf_id}/run", headers=other_headers, json={"input": {}})
    assert r.status_code in (403, 404)

    r = client.get("/api/workflows", headers=other_headers)
    assert all(w["id"] != wf_id for w in r.json())


def test_webhook_isolation_and_secret(client, auth_headers):
    webhook_nodes = [
        {"id": "w1", "type": "webhook", "name": "Hook", "position": {"x": 0, "y": 0}, "config": {}},
        {
            "id": "w2",
            "type": "log",
            "name": "Echo",
            "position": {"x": 150, "y": 0},
            "config": {"message": "webhook got {{input.amount}}"},
        },
    ]
    edges = [{"id": "we1", "source": "w1", "target": "w2"}]

    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "HookWF", "published": True, "webhook_secret": "s3cret", "nodes": webhook_nodes, "edges": edges},
    )
    wf_id = r.json()["id"]

    # Unpublished check: create another unpublished webhook workflow.
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "Unpub", "published": False, "nodes": webhook_nodes, "edges": edges},
    )
    unpublished_id = r.json()["id"]
    r = client.post(f"/api/webhooks/{unpublished_id}", json={"amount": 5})
    assert r.status_code == 403

    # Wrong secret
    r = client.post(f"/api/webhooks/{wf_id}", json={"amount": 5}, headers={"X-Webhook-Secret": "wrong"})
    assert r.status_code == 401

    # No secret
    r = client.post(f"/api/webhooks/{wf_id}", json={"amount": 5})
    assert r.status_code == 401

    # Correct secret (public endpoint, no auth headers needed)
    r = client.post(f"/api/webhooks/{wf_id}", json={"amount": 1500}, headers={"X-Webhook-Secret": "s3cret"})
    assert r.status_code == 200, r.text
    assert r.json() == {"logged": "webhook got 1500"}


def test_webhook_unknown_id(client):
    r = client.post("/api/webhooks/not-real", json={})
    assert r.status_code == 404
    assert r.json() == {"error": "Workflow not found"}


def test_webhook_unpublished_body(client, auth_headers):
    nodes = [
        {"id": "w1", "type": "webhook", "name": "Hook", "position": {"x": 0, "y": 0}, "config": {}},
        {
            "id": "w2",
            "type": "log",
            "name": "Echo",
            "position": {"x": 150, "y": 0},
            "config": {"message": "webhook got {{input.amount}}"},
        },
    ]
    edges = [{"id": "we1", "source": "w1", "target": "w2"}]
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "Unpub", "published": False, "nodes": nodes, "edges": edges},
    )
    wf_id = r.json()["id"]
    r = client.post(f"/api/webhooks/{wf_id}", json={"amount": 5})
    assert r.status_code == 403
    assert r.json() == {"error": "Workflow is not published"}


def test_webhook_failed_execution_returns_500(client, auth_headers):
    nodes = [
        {"id": "w1", "type": "webhook", "name": "Hook", "position": {"x": 0, "y": 0}, "config": {}},
        {
            "id": "b",
            "type": "condition",
            "name": "Bad",
            "position": {"x": 150, "y": 0},
            "config": {"expression": "nodes.missing.output.x > 1"},
        },
    ]
    edges = [{"id": "we1", "source": "w1", "target": "b"}]
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={"name": "BadWF", "published": True, "nodes": nodes, "edges": edges},
    )
    wf_id = r.json()["id"]
    r = client.post(f"/api/webhooks/{wf_id}", json={"amount": 5})
    assert r.status_code == 500
    assert r.json() == {"error": "Workflow execution failed"}


def test_invalid_workflow_rejected(client, auth_headers):
    # Drafts may be saved while incomplete (no trigger)...
    r = client.post(
        "/api/workflows",
        headers=auth_headers,
        json={
            "name": "Draft",
            "nodes": [{"id": "x1", "type": "log", "name": "L", "position": {"x": 0, "y": 0}, "config": {}}],
            "edges": [],
        },
    )
    assert r.status_code == 201
    wf_id = r.json()["id"]

    # ...but execution must validate and record the failure.
    r = client.post(f"/api/workflows/{wf_id}/run", headers=auth_headers, json={"input": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "trigger" in (body["error"] or "")