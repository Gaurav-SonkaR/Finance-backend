from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.schemas import UserUpdateRequest


def get_all_users(db: Session, role=None, user_status=None, page: int = 1, limit: int = 20):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if user_status:
        query = query.filter(User.status == user_status)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return users, total


def get_user_by_id(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def update_user(db: Session, user_id: str, payload: UserUpdateRequest, current_user: User) -> User:
    user = get_user_by_id(db, user_id)

    # Prevent admin from deactivating or demoting themselves
    if user_id == current_user.id:
        if payload.status and payload.status.value == "inactive":
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")
        if payload.role and payload.role.value != "admin":
            raise HTTPException(status_code=400, detail="You cannot change your own role.")

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.status is not None:
        user.status = payload.status

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str, current_user: User):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()
