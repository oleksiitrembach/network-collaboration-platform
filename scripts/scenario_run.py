from __future__ import annotations

import json
import socket
import ssl
import time
import uuid
from pprint import pprint

import httpx
import websockets

BASE_URL = "https://127.0.0.1:8443"


def print_step(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    client = httpx.Client(verify=False, timeout=10.0)
    suffix = uuid.uuid4().hex[:8]
    admin_name = f"admin_demo_{suffix}"
    user_name = f"user_demo_{suffix}"

    print_step("1) Health")
    health = client.get(f"{BASE_URL}/api/v1/health")
    print("status:", health.status_code)
    print("body:", health.text)

    print_step("2) Register admin")
    reg_admin = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": admin_name, "password": "Secure123"},
    )
    print("status:", reg_admin.status_code)
    admin_json = reg_admin.json()
    pprint(admin_json)
    admin_token = admin_json["token"]

    print_step("3) Register user")
    reg_user = client.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": user_name, "password": "Secure123"},
    )
    print("status:", reg_user.status_code)
    user_json = reg_user.json()
    pprint(user_json)
    user_token = user_json["token"]

    print_step("4) Create task as admin")
    task = client.post(
        f"{BASE_URL}/api/v1/tasks",
        headers={"X-Auth-Token": admin_token},
        json={"title": "Task demo", "description": "Walidacja end-to-end"},
    )
    print("status:", task.status_code)
    pprint(task.json())

    print_step("5) GraphQL me + tasks")
    gql = client.post(
        f"{BASE_URL}/graphql",
        headers={"X-Auth-Token": admin_token},
        json={"query": "query { me { username role } tasks { id title owner } }"},
    )
    print("status:", gql.status_code)
    pprint(gql.json())

    print_step("6) RBAC check (user on admin endpoint)")
    deny = client.get(
        f"{BASE_URL}/api/v1/admin/audit-logs",
        headers={"X-Auth-Token": user_token},
    )
    print("status:", deny.status_code)
    print("body:", deny.text)

    print_step("7) Admin audit logs")
    logs = client.get(
        f"{BASE_URL}/api/v1/admin/audit-logs",
        headers={"X-Auth-Token": admin_token},
    )
    print("status:", logs.status_code)
    data = logs.json()
    print("entries:", len(data))
    print("latest:")
    pprint(data[:3])

    print_step("8) WebSocket handshake + echo")
    ssl_context = ssl._create_unverified_context()

    async def ws_check() -> None:
        url = f"wss://127.0.0.1:8443/ws/notifications?token={admin_token}"
        async with websockets.connect(url, ssl=ssl_context) as ws:
            connected = await ws.recv()
            print("connected event:", connected)
            await ws.send("ping-demo")
            echoed = await ws.recv()
            print("echo event:", echoed)

    import asyncio

    asyncio.run(ws_check())

    print_step("9) TCP socket broadcast")
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect(("127.0.0.1", 9000))
    s2.connect(("127.0.0.1", 9000))
    s1.recv(4096)
    s2.recv(4096)
    s1.sendall(b"NICK:demo1\n")
    s2.sendall(b"NICK:demo2\n")
    s1.recv(4096)
    s2.recv(4096)
    s1.sendall(b"MSG:wiadomosc testowa\n")
    s2.settimeout(2)
    message = ""
    start = time.time()
    while time.time() - start < 2:
        chunk = s2.recv(4096).decode("utf-8", errors="ignore")
        if "[demo1] wiadomosc testowa" in chunk:
            message = "[demo1] wiadomosc testowa"
            break
    if not message:
        message = "Nie wykryto oczekiwanego broadcastu w oknie czasowym"
    print("client2 received:", message)
    s1.sendall(b"QUIT\n")
    s2.sendall(b"QUIT\n")
    s1.close()
    s2.close()

    print_step("Scenario finished")
    print("Wszystkie kluczowe scenariusze wykonane.")


if __name__ == "__main__":
    main()
