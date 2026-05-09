from __future__ import annotations

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from app.main import create_app


def test_register_login_and_create_task(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path, bootstrap_admin_enabled=False)
    client = TestClient(app)

    register_response = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){register(username:$u,password:$p){token username role}}",
            "variables": {"u": "alice", "p": "Secure123"},
        },
    )
    assert register_response.status_code == 200
    data = register_response.json()["data"]["register"]
    token = data["token"]
    assert data["role"] == "admin"

    login_response = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){login(username:$u,password:$p){token username role}}",
            "variables": {"u": "alice", "p": "Secure123"},
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["data"]["login"]["role"] == "admin"

    create_task_response = client.post(
        "/graphql",
        headers={"X-Auth-Token": token},
        json={
            "query": "mutation($t:String!,$d:String!){createTask(title:$t,description:$d){id title description owner}}",
            "variables": {"t": "Przygotowac demo", "d": "Scenariusz prezentacji"},
        },
    )
    assert create_task_response.status_code == 200
    assert create_task_response.json()["data"]["createTask"]["title"] == "Przygotowac demo"

    list_response = client.post(
        "/graphql",
        headers={"X-Auth-Token": token},
        json={"query": "query { tasks { id title owner } }"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]["tasks"]) == 1

    logs_response = client.post(
        "/graphql",
        headers={"X-Auth-Token": token},
        json={"query": "query { auditLogs(limit: 200) { id eventType actor result details createdAt } }"},
    )
    assert logs_response.status_code == 200
    logs = logs_response.json()["data"]["auditLogs"]
    assert any(item["eventType"] == "task.create" for item in logs)


def test_admin_endpoint_is_protected_by_role(tmp_path: Path) -> None:
    db_path = str(tmp_path / "rbac.db")
    app = create_app(db_path=db_path, bootstrap_admin_enabled=False)
    client = TestClient(app)

    admin_register = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){register(username:$u,password:$p){token username role}}",
            "variables": {"u": "adminuser", "p": "Secure123"},
        },
    )
    assert admin_register.status_code == 200

    user_register = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){register(username:$u,password:$p){token username role}}",
            "variables": {"u": "bob", "p": "Secure123"},
        },
    )
    assert user_register.status_code == 200
    assert user_register.json()["data"]["register"]["role"] == "user"

    user_login = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){login(username:$u,password:$p){token}}",
            "variables": {"u": "bob", "p": "Secure123"},
        },
    )
    assert user_login.status_code == 200
    user_token = user_login.json()["data"]["login"]["token"]

    forbidden_response = client.post(
        "/graphql",
        headers={"X-Auth-Token": user_token},
        json={"query": "query { auditLogs { id eventType } }"},
    )
    assert forbidden_response.status_code == 200
    assert "errors" in forbidden_response.json()
    assert any("Dostep tylko dla administratora" in e.get("message", "") for e in forbidden_response.json()["errors"])


def test_graphql_queries_work_for_authenticated_user(tmp_path: Path) -> None:
    db_path = str(tmp_path / "graphql.db")
    app = create_app(db_path=db_path, bootstrap_admin_enabled=False)
    client = TestClient(app)

    register_response = client.post(
        "/graphql",
        json={
            "query": "mutation($u:String!,$p:String!){register(username:$u,password:$p){token}}",
            "variables": {"u": "alice", "p": "Secure123"},
        },
    )
    token = register_response.json()["data"]["register"]["token"]

    client.post(
        "/graphql",
        headers={"X-Auth-Token": token},
        json={
            "query": "mutation($t:String!,$d:String!){createTask(title:$t,description:$d){id}}",
            "variables": {"t": "Task gql", "d": "GraphQL visibility"},
        },
    )

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
    app = create_app(db_path=db_path, bootstrap_admin_enabled=False)
    client = TestClient(app)

    with pytest.raises(Exception):
        with client.websocket_connect("/ws/notifications?token=invalid"):
            pass
