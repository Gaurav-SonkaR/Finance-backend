from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.services.auth_service import register_user, login_user
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=201, summary="Register a new user")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user. Default role is **viewer**.

    Roles available:
    - **viewer** – read-only access to dashboard overview
    - **analyst** – read access + detailed analytics
    - **admin** – full access: create, update, delete records and manage users
    """
    user, token = register_user(db, payload)
    return {
        "success": True,
        "message": "Registration successful.",
        "data": UserOut.model_validate(user).model_dump(),
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=dict, summary="Login and get access token")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password. Returns a JWT bearer token."""
    user, token = login_user(db, payload)
    return {
        "success": True,
        "message": "Login successful.",
        "data": UserOut.model_validate(user).model_dump(),
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=dict, summary="Get current authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return {
        "success": True,
        "data": UserOut.model_validate(current_user).model_dump(),
    }
