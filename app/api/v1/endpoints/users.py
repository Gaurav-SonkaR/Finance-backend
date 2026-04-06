from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.schemas import UserOut, UserUpdateRequest
from app.services import user_service
from app.middleware.auth import require_admin
from app.models.user import User, UserRole, UserStatus
import math

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/", response_model=dict, summary="List all users (Admin only)")
def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users with optional role/status filtering and pagination."""
    users, total = user_service.get_all_users(db, role=role, user_status=status, page=page, limit=limit)
    return {
        "success": True,
        "data": [UserOut.model_validate(u).model_dump() for u in users],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total / limit),
        },
    }


@router.get("/{user_id}", response_model=dict, summary="Get user by ID (Admin only)")
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Retrieve a specific user by their ID."""
    user = user_service.get_user_by_id(db, user_id)
    return {"success": True, "data": UserOut.model_validate(user).model_dump()}


@router.patch("/{user_id}", response_model=dict, summary="Update user role/status (Admin only)")
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's name, role, or status. Admins cannot deactivate themselves."""
    user = user_service.update_user(db, user_id, payload, current_user)
    return {"success": True, "message": "User updated successfully.", "data": UserOut.model_validate(user).model_dump()}


@router.delete("/{user_id}", response_model=dict, summary="Delete a user (Admin only)")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Permanently delete a user. Admins cannot delete their own account."""
    user_service.delete_user(db, user_id, current_user)
    return {"success": True, "message": "User deleted successfully."}
