"""
Auth schemas
"""
from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: int
    username: str


class UserInfo(BaseModel):
    username: str
    tenant_id: int
    tenant_name: Optional[str] = None
