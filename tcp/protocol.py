from __future__ import annotations

# Simple text protocol over TCP:
# NICK:<username> - register client display name
# MSG:<message> - broadcast message to all connected clients
# QUIT - close connection

NICK_PREFIX = "NICK:"
MSG_PREFIX = "MSG:"
QUIT = "QUIT"
