from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import strawberry
from fastapi import HTTPException, Request, status
from strawberry.fastapi import BaseContext
from strawberry.types import Info

from app.config import KAFKA_TOPIC_AUDIT, KAFKA_TOPIC_TASKS
from app.db import Database, User


@strawberry.type
class GraphQLTask:
    id: int
    title: str
    description: str
    owner: str
    created_at: datetime


@strawberry.type
class GraphQLUser:
    id: int
    username: str
    role: str


@strawberry.type
class GraphQLAuditLog:
    id: int
    event_type: str
    actor: str
    result: str
    details: str
    created_at: datetime


@strawberry.type
class GraphQLAuthResponse:
    token: str
    username: str
    role: str


@dataclass
class GraphQLContext(BaseContext):
    db: Database
    user: User | None
    publisher: "EventPublisher" | None = None
    hub: "WebSocketHub" | None = None


def _audit(ctx: GraphQLContext, event_type: str, actor: str, result: str, details: str) -> None:
    ctx.db.log_event(event_type, actor, result, details)
    if ctx.publisher is not None:
        ctx.publisher.publish(
            KAFKA_TOPIC_AUDIT,
            {"event": event_type, "actor": actor, "result": result, "details": details},
            key=actor,
        )


def build_context_factory(db: Database, publisher=None, hub=None):
    async def get_context(request: Request) -> GraphQLContext:
        token = request.headers.get("X-Auth-Token")
        if not token:
            return GraphQLContext(db=db, user=None, publisher=publisher, hub=hub)

        user = db.get_user_by_token(token)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidlowy token autoryzacyjny.")

        return GraphQLContext(db=db, user=user, publisher=publisher, hub=hub)

    return get_context


def _require_auth(ctx: GraphQLContext) -> User:
    if ctx.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Brak tokenu autoryzacyjnego.")
    return ctx.user


def _require_admin(ctx: GraphQLContext) -> User:
    user = _require_auth(ctx)
    if user.role != "admin":
        _audit(ctx, "auth.rbac", user.username, "denied", "Proba dostepu do zasobu administracyjnego")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dostep tylko dla administratora.")
    return user


@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: Info[GraphQLContext, None]) -> GraphQLUser:
        user = _require_auth(info.context)
        return GraphQLUser(id=user.id, username=user.username, role=user.role)

    @strawberry.field
    def tasks(self, info: Info[GraphQLContext, None]) -> list[GraphQLTask]:
        _require_auth(info.context)
        db = info.context.db
        return [
            GraphQLTask(
                id=task.id,
                title=task.title,
                description=task.description,
                owner=task.owner,
                created_at=task.created_at,
            )
            for task in db.list_tasks()
        ]

    @strawberry.field
    def audit_logs(self, info: Info[GraphQLContext, None], limit: int = 100) -> list[GraphQLAuditLog]:
        _require_admin(info.context)
        db = info.context.db
        return [
            GraphQLAuditLog(
                id=entry.id,
                event_type=entry.event_type,
                actor=entry.actor,
                result=entry.result,
                details=entry.details,
                created_at=entry.created_at,
            )
            for entry in db.list_audit_logs(limit=limit)
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def register(self, info: Info[GraphQLContext, None], username: str, password: str) -> GraphQLAuthResponse:
        db = info.context.db
        try:
            user = db.register_user(username, password)
        except Exception:
            _audit(info.context, "auth.register", username, "denied", "Konflikt nazwy uzytkownika")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Uzytkownik o podanej nazwie juz istnieje.")

        token = db.authenticate_user(username, password)
        if token is None:
            _audit(info.context, "auth.register", username, "error", "Brak tokenu po rejestracji")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Nie udalo sie utworzyc sesji.")

        _audit(info.context, "auth.register", username, "ok", f"Utworzono konto z rola {user.role}")
        return GraphQLAuthResponse(token=token, username=user.username, role=user.role)

    @strawberry.mutation
    def login(self, info: Info[GraphQLContext, None], username: str, password: str) -> GraphQLAuthResponse:
        db = info.context.db
        token = db.authenticate_user(username, password)
        if token is None:
            _audit(info.context, "auth.login", username, "denied", "Nieprawidlowe dane logowania")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidlowe dane logowania.")

        user = db.get_user_by_username(username)
        if user is None:
            _audit(info.context, "auth.login", username, "error", "Brak uzytkownika po poprawnym logowaniu")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Niespojnosc danych uzytkownika.")

        _audit(info.context, "auth.login", username, "ok", f"Logowanie z rola {user.role}")
        return GraphQLAuthResponse(token=token, username=user.username, role=user.role)

    @strawberry.mutation
    async def create_task(self, info: Info[GraphQLContext, None], title: str, description: str) -> GraphQLTask:
        from app.realtime import WebSocketHub

        user = _require_auth(info.context)
        db = info.context.db
        task = db.create_task(title, description, user.id)

        _audit(info.context, "task.create", user.username, "ok", f"Utworzono zadanie o id {task.id}")

        if info.context.publisher is not None:
            info.context.publisher.publish(
                KAFKA_TOPIC_TASKS,
                {"event": "task_created", "task_id": task.id, "title": task.title, "owner": user.username},
                key=user.username,
            )

        if info.context.hub is not None:
            await info.context.hub.broadcast(
                {
                    "event": "task_created",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "owner": task.owner,
                        "created_at": task.created_at.isoformat(),
                    },
                    "by": user.username,
                }
            )

        return GraphQLTask(
            id=task.id,
            title=task.title,
            description=task.description,
            owner=task.owner,
            created_at=task.created_at,
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
