from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str
    role: str


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=600)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    owner: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    service: str


class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    actor: str
    result: str
    details: str
    created_at: datetime
