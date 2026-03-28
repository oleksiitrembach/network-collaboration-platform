from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlite3 import IntegrityError
from strawberry.fastapi import GraphQLRouter

from app.config import (
    BOOTSTRAP_ADMIN_ENABLED,
    BOOTSTRAP_ADMIN_PASSWORD,
    BOOTSTRAP_ADMIN_USERNAME,
    DB_PATH,
    KAFKA_TOPIC_AUDIT,
    KAFKA_TOPIC_TASKS,
)
from app.db import Database, User
from app.events import EventPublisher
from app.graphql_api import build_context_factory, schema
from app.realtime import WebSocketHub
from app.schemas import (
    AuditLogResponse,
    AuthResponse,
    HealthResponse,
    LoginRequest,
    RegisterRequest,
    TaskCreateRequest,
    TaskResponse,
)


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
        description="Projekt PAS: REST over HTTPS + WebSocket + TCP socket service.",
        lifespan=app_lifespan,
    )

    db = Database(db_path)
    hub = WebSocketHub()
    publisher = EventPublisher()
    app.state.publisher = publisher

    graphql_router = GraphQLRouter(schema=schema, context_getter=build_context_factory(db))
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

    @app.post("/api/v1/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
    def register(payload: RegisterRequest) -> AuthResponse:
        try:
            user = db.register_user(payload.username, payload.password)
        except IntegrityError as ex:
            audit("auth.register", payload.username, "denied", "Konflikt nazwy uzytkownika")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Uzytkownik o podanej nazwie juz istnieje.",
            ) from ex

        token = db.authenticate_user(payload.username, payload.password)
        if token is None:
            audit("auth.register", payload.username, "error", "Brak tokenu po rejestracji")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nie udalo sie utworzyc sesji.",
            )
        audit("auth.register", payload.username, "ok", f"Utworzono konto z rola {user.role}")
        return AuthResponse(token=token, username=user.username, role=user.role)

    @app.post("/api/v1/auth/login", response_model=AuthResponse)
    def login(payload: LoginRequest) -> AuthResponse:
        token = db.authenticate_user(payload.username, payload.password)
        if token is None:
            audit("auth.login", payload.username, "denied", "Nieprawidlowe dane logowania")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidlowe dane logowania.",
            )
        user = db.get_user_by_username(payload.username)
        if user is None:
            audit("auth.login", payload.username, "error", "Brak uzytkownika po poprawnym logowaniu")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Niespojnosc danych uzytkownika.",
            )
        audit("auth.login", payload.username, "ok", f"Logowanie z rola {user.role}")
        return AuthResponse(token=token, username=payload.username, role=user.role)

    @app.get("/api/v1/tasks", response_model=list[TaskResponse])
    def list_tasks(_: User = Depends(get_current_user)) -> list[TaskResponse]:
        tasks = db.list_tasks()
        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                owner=task.owner,
                created_at=task.created_at,
            )
            for task in tasks
        ]

    @app.post("/api/v1/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
    async def create_task(payload: TaskCreateRequest, user: User = Depends(get_current_user)) -> TaskResponse:
        task = db.create_task(payload.title, payload.description, user.id)
        audit("task.create", user.username, "ok", f"Utworzono zadanie o id {task.id}")
        publisher.publish(
            KAFKA_TOPIC_TASKS,
            {
                "event": "task_created",
                "task_id": task.id,
                "title": task.title,
                "owner": user.username,
            },
            key=user.username,
        )
        response = TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            owner=task.owner,
            created_at=task.created_at,
        )
        await hub.broadcast(
            {
                "event": "task_created",
                "task": response.model_dump(mode="json"),
                "by": user.username,
            }
        )
        return response

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

    @app.get("/api/v1/admin/audit-logs", response_model=list[AuditLogResponse])
    def get_audit_logs(_: User = Depends(require_admin)) -> list[AuditLogResponse]:
        logs = db.list_audit_logs(limit=200)
        return [
            AuditLogResponse(
                id=entry.id,
                event_type=entry.event_type,
                actor=entry.actor,
                result=entry.result,
                details=entry.details,
                created_at=entry.created_at,
            )
            for entry in logs
        ]

    return app


app = create_app()
