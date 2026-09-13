import os
import sys

import pytest

# Configure a dedicated test database BEFORE importing the app so that
# app.core.config picks it up (env vars take precedence over .env).
os.environ["DATABASE_URL"] = "sqlite:///./test_flow_api.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SECRET_ENCRYPTION_KEY"] = "mUiG1budkRLo6fHV1kahSXuy6srno1Uf4hzL_a7OxtI="
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import app.nodes  # noqa: F401, E402  (register nodes)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    engine_url = os.environ["DATABASE_URL"]
    db_file = engine_url.replace("sqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)
    with TestClient(app) as c:
        yield c
    # Dispose pooled connections so the file can be removed on Windows.
    from app.core import database as dbmod

    dbmod.engine.dispose()
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="session")
def auth_headers(client):
    email = "a@test.com"
    password = "password123"
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}