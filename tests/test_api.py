from __future__ import annotations

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from app.main import create_app


def test_register_login_and_create_task(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path)
    client = TestClient(app)

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "Secure123"},
    )
    assert register_response.status_code == 201
    token = register_response.json()["token"]
    assert register_response.json()["role"] == "admin"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "Secure123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["role"] == "admin"

    create_task_response = client.post(
        "/api/v1/tasks",
        headers={"X-Auth-Token": token},
        json={"title": "Przygotowac demo", "description": "Scenariusz prezentacji"},
    )
    assert create_task_response.status_code == 201
    assert create_task_response.json()["title"] == "Przygotowac demo"

    list_response = client.get(
        "/api/v1/tasks",
        headers={"X-Auth-Token": token},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    logs_response = client.get(
        "/api/v1/admin/audit-logs",
        headers={"X-Auth-Token": token},
    )
    assert logs_response.status_code == 200
    assert any(item["event_type"] == "task.create" for item in logs_response.json())


def test_admin_endpoint_is_protected_by_role(tmp_path: Path) -> None:
    db_path = str(tmp_path / "rbac.db")
    app = create_app(db_path=db_path)
    client = TestClient(app)

    admin_register = client.post(
        "/api/v1/auth/register",
        json={"username": "adminuser", "password": "Secure123"},
    )
    assert admin_register.status_code == 201

    user_register = client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "password": "Secure123"},
    )
    assert user_register.status_code == 201
    assert user_register.json()["role"] == "user"

    user_login = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "Secure123"},
    )
    assert user_login.status_code == 200

    forbidden_response = client.get(
        "/api/v1/admin/audit-logs",
        headers={"X-Auth-Token": user_login.json()["token"]},
    )
    assert forbidden_response.status_code == 403


def test_graphql_queries_work_for_authenticated_user(tmp_path: Path) -> None:
    db_path = str(tmp_path / "graphql.db")
    app = create_app(db_path=db_path)
    client = TestClient(app)

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "Secure123"},
    )
    token = register_response.json()["token"]

    create_task_response = client.post(
        "/api/v1/tasks",
        headers={"X-Auth-Token": token},
        json={"title": "Task gql", "description": "GraphQL visibility"},
    )
    assert create_task_response.status_code == 201

    graphql_response = client.post(
        "/graphql",
        headers={"X-Auth-Token": token},
        json={"query": "query { me { username role } tasks { title owner } }"},
    )
    assert graphql_response.status_code == 200
    payload = graphql_response.json()
    assert payload["data"]["me"]["username"] == "alice"
    assert any(task["title"] == "Task gql" for task in payload["data"]["tasks"])


def test_websocket_requires_valid_token(tmp_path: Path) -> None:
    db_path = str(tmp_path / "ws.db")
    app = create_app(db_path=db_path)
    client = TestClient(app)

    with pytest.raises(Exception):
        with client.websocket_connect("/ws/notifications?token=invalid"):
            pass
