from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import strawberry
from fastapi import HTTPException, Request, status
from strawberry.fastapi import BaseContext

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


@dataclass
class GraphQLContext(BaseContext):
    db: Database
    user: User


def build_context_factory(db: Database):
    async def get_context(request: Request) -> GraphQLContext:
        token = request.headers.get("X-Auth-Token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Brak tokenu autoryzacyjnego.")

        user = db.get_user_by_token(token)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidlowy token autoryzacyjny.")

        return GraphQLContext(db=db, user=user)

    return get_context


@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: strawberry.Info[GraphQLContext, None]) -> GraphQLUser:
        user = info.context.user
        return GraphQLUser(id=user.id, username=user.username, role=user.role)

    @strawberry.field
    def tasks(self, info: strawberry.Info[GraphQLContext, None]) -> list[GraphQLTask]:
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
    def audit_logs(self, info: strawberry.Info[GraphQLContext, None], limit: int = 100) -> list[GraphQLAuditLog]:
        user = info.context.user
        if user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dostep tylko dla administratora.")

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


schema = strawberry.Schema(query=Query)
