from __future__ import annotations

import socket
import threading

from app.config import TCP_HOST, TCP_PORT
from tcp.protocol import MSG_PREFIX, NICK_PREFIX, QUIT


def receiver(sock: socket.socket) -> None:
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("Server closed connection.")
                break
            print(data.decode("utf-8", errors="ignore").strip())
        except OSError:
            break


def main() -> None:
    host = input(f"Host [{TCP_HOST}]: ").strip() or TCP_HOST
    raw_port = input(f"Port [{TCP_PORT}]: ").strip()
    port = int(raw_port) if raw_port else TCP_PORT

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        thread = threading.Thread(target=receiver, args=(sock,), daemon=True)
        thread.start()

        nickname = input("Nickname: ").strip() or "student"
        sock.sendall(f"{NICK_PREFIX}{nickname}\n".encode("utf-8"))

        print("Type messages and press Enter. /quit closes the client.")
        while True:
            text = input().strip()
            if text.lower() == "/quit":
                sock.sendall(f"{QUIT}\n".encode("utf-8"))
                break
            sock.sendall(f"{MSG_PREFIX}{text}\n".encode("utf-8"))


if __name__ == "__main__":
    main()
