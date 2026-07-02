from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.security import create_access_token, hash_password, verify_password


def register_user(db: Session, email: str, full_name: str, password: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("A user with this email already exists.")
    # first registered user becomes admin so the demo always has one
    is_first_user = db.query(User).count() == 0
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN if is_first_user else UserRole.RECRUITER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def issue_token(user: User) -> str:
    return create_access_token(subject=user.email)
