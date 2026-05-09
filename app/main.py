from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from strawberry.fastapi import GraphQLRouter

from app.config import (
    BOOTSTRAP_ADMIN_ENABLED,
    BOOTSTRAP_ADMIN_PASSWORD,
    BOOTSTRAP_ADMIN_USERNAME,
    DB_PATH,
    KAFKA_TOPIC_AUDIT,
)
from app.db import Database, User
from app.events import EventPublisher
from app.graphql_api import build_context_factory, schema
from app.realtime import WebSocketHub
from app.schemas import HealthResponse


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    try:
        yield
    finally:
        publisher = getattr(app.state, "publisher", None)
        if publisher is not None:
            publisher.close()


def create_app(
    db_path: str = DB_PATH,
    bootstrap_admin_enabled: bool = BOOTSTRAP_ADMIN_ENABLED,
    bootstrap_admin_username: str = BOOTSTRAP_ADMIN_USERNAME,
    bootstrap_admin_password: str = BOOTSTRAP_ADMIN_PASSWORD,
) -> FastAPI:
    app = FastAPI(
        title="Network Collaboration Platform",
        version="1.0.0",
        description="Network Collaboration Platform: GraphQL over HTTPS + WebSocket + TCP socket service.",
        lifespan=app_lifespan,
        docs_url=None,
        redoc_url=None,
    )

    db = Database(db_path)
    ui_file_path = Path(__file__).resolve().parent / "ui" / "index.html"
    hub = WebSocketHub()
    publisher = EventPublisher()
    app.state.publisher = publisher
    app.state.hub = hub

    graphql_router = GraphQLRouter(
        schema=schema,
        context_getter=build_context_factory(db, publisher, hub),
    )
    app.include_router(graphql_router, prefix="/graphql")

    def audit(event_type: str, actor: str, result: str, details: str) -> None:
        db.log_event(event_type, actor, result, details)
        publisher.publish(
            KAFKA_TOPIC_AUDIT,
            {
                "event": event_type,
                "actor": actor,
                "result": result,
                "details": details,
            },
            key=actor,
        )

    if bootstrap_admin_enabled:
        bootstrap_user = db.ensure_admin_user(bootstrap_admin_username, bootstrap_admin_password)
        audit(
            "auth.bootstrap",
            bootstrap_user.username,
            "ok",
            "Automatycznie zapewniono konto administratora przy starcie aplikacji",
        )

    def get_current_user(x_auth_token: str = Header(alias="X-Auth-Token")) -> User:
        user = db.get_user_by_token(x_auth_token)
        if user is None:
            audit("auth.token", "anonymous", "denied", "Nieprawidlowy token autoryzacyjny")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidlowy token autoryzacyjny.",
            )
        return user

    def require_admin(user: User = Depends(get_current_user)) -> User:
        if user.role != "admin":
            audit("auth.rbac", user.username, "denied", "Proba dostepu do endpointu administracyjnego")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dostep tylko dla administratora.",
            )
        return user

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="network-collaboration-platform")

    @app.get("/", include_in_schema=False)
    def ui() -> FileResponse:
        return FileResponse(ui_file_path)

    @app.websocket("/ws/notifications")
    async def notifications(websocket: WebSocket, token: str) -> None:
        user = db.get_user_by_token(token)
        if user is None:
            audit("ws.connect", "anonymous", "denied", "Proba polaczenia WebSocket z nieprawidlowym tokenem")
            await websocket.close(code=1008)
            return

        await hub.connect(user.username, websocket)
        audit("ws.connect", user.username, "ok", "Nawiazano polaczenie WebSocket")
        await websocket.send_json(
            {
                "event": "connected",
                "message": f"Polaczono z kanalem powiadomien jako {user.username}.",
            }
        )

        try:
            while True:
                payload = await websocket.receive_text()
                await websocket.send_json(
                    {
                        "event": "echo",
                        "message": payload,
                    }
                )
        except WebSocketDisconnect:
            audit("ws.disconnect", user.username, "ok", "Rozlaczono WebSocket")
            await hub.disconnect(user.username, websocket)

    return app


app = create_app()
