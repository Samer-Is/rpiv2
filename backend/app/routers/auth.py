"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.schemas.auth import TokenResponse
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["Auth"])

# Temporary hardcoded user for scaffold (will be replaced with DB lookup in CHUNK 2)
TEMP_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": get_password_hash("admin123"),
        "tenant_id": 1,  # YELO tenant
        "tenant_name": "YELO"
    }
}


@router.post("/login", response_model=TokenResponse)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login and get JWT token with tenant_id claim"""
    user = TEMP_USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(data={
        "sub": user["username"],
        "tenant_id": user["tenant_id"],
        "tenant_name": user["tenant_name"]
    })
    
    return TokenResponse(
        access_token=token,
        tenant_id=user["tenant_id"],
        username=user["username"]
    )
