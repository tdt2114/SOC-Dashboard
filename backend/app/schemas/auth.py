from __future__ import annotations

from pydantic import BaseModel


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthLogoutRequest(BaseModel):
    refresh_token: str


class AuthUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    department: str | None = None
    roles: list[str]


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class AuthProfileUpdateRequest(BaseModel):
    email: str
    full_name: str | None = None


class AuthChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
