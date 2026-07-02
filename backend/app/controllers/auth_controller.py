from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas import TokenOut, UserCreate, UserLogin
from app.services.auth_service import authenticate_user, issue_token, register_user


def handle_register(db: Session, payload: UserCreate) -> TokenOut:
    try:
        user = register_user(db, payload.email, payload.full_name, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = issue_token(user)
    return TokenOut(access_token=token, user=user)


def handle_login(db: Session, payload: UserLogin) -> TokenOut:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = issue_token(user)
    return TokenOut(access_token=token, user=user)
