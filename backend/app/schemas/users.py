from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentOptionResponse(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool


class RoleOptionResponse(BaseModel):
    id: int
    name: str
    is_active: bool


class UserAdminItemResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    department: str | None = None
    department_id: int | None = None
    roles: list[str]
    created_at: datetime


class UserAdminListResponse(BaseModel):
    items: list[UserAdminItemResponse]
    total: int
    departments: list[DepartmentOptionResponse]
    roles: list[RoleOptionResponse]


class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=8)
    full_name: str | None = None
    department_id: int | None = None
    is_active: bool = True
    is_superuser: bool = False
    roles: list[str]


class UserUpdateRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    roles: list[str] | None = None


class UserResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
