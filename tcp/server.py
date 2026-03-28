from __future__ import annotations

import socket
import threading
from dataclasses import dataclass

from app.config import TCP_HOST, TCP_PORT
from tcp.protocol import MSG_PREFIX, NICK_PREFIX, QUIT


@dataclass
class ClientSession:
    conn: socket.socket
    addr: tuple[str, int]
    username: str = "anonymous"


class TcpChatServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients: list[ClientSession] = []
        self.clients_lock = threading.Lock()

    def broadcast(self, message: str, sender_conn: socket.socket | None = None) -> None:
        payload = f"{message}\n".encode("utf-8")
        to_remove: list[ClientSession] = []

        with self.clients_lock:
            for session in self.clients:
                if sender_conn is not None and session.conn is sender_conn:
                    continue
                try:
                    session.conn.sendall(payload)
                except OSError:
                    to_remove.append(session)

            for session in to_remove:
                if session in self.clients:
                    self.clients.remove(session)

    def handle_client(self, session: ClientSession) -> None:
        conn = session.conn
        addr = session.addr
        conn.sendall(b"Connected to TCP chat server. Use NICK:<name>, MSG:<text>, QUIT\n")
        self.broadcast(f"[SYSTEM] New connection from {addr[0]}:{addr[1]}")

        try:
            with conn:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break

                    text = data.decode("utf-8", errors="ignore").strip()
                    if not text:
                        continue

                    if text == QUIT:
                        conn.sendall(b"Bye\n")
                        break

                    if text.startswith(NICK_PREFIX):
                        nickname = text[len(NICK_PREFIX) :].strip()
                        if not nickname:
                            conn.sendall(b"Invalid nickname\n")
                            continue
                        old_name = session.username
                        session.username = nickname
                        conn.sendall(f"Nickname set to {nickname}\n".encode("utf-8"))
                        self.broadcast(f"[SYSTEM] {old_name} is now known as {nickname}", sender_conn=conn)
                        continue

                    if text.startswith(MSG_PREFIX):
                        content = text[len(MSG_PREFIX) :].strip()
                        if not content:
                            conn.sendall(b"Empty message\n")
                            continue
                        self.broadcast(f"[{session.username}] {content}")
                        continue

                    conn.sendall(b"Unsupported command\n")
        except ConnectionError:
            pass
        finally:
            with self.clients_lock:
                if session in self.clients:
                    self.clients.remove(session)
            self.broadcast(f"[SYSTEM] {session.username} disconnected")

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"TCP chat server listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                session = ClientSession(conn=conn, addr=addr)
                with self.clients_lock:
                    self.clients.append(session)
                thread = threading.Thread(target=self.handle_client, args=(session,), daemon=True)
                thread.start()
        except KeyboardInterrupt:
            print("Stopping TCP chat server...")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    TcpChatServer(TCP_HOST, TCP_PORT).start()
