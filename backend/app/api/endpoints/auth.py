from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    DemoLoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Citizen & User Registration")
async def register(user_in: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user (Citizen or Admin) and returns JWT access token.
    """
    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Restrict admin self-registration if necessary, or allow designated role
    role = "admin" if user_in.role == "admin" else "citizen"

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user.to_dict(),
    }


@router.post("/login", response_model=TokenResponse, summary="User Authentication & Token Issuance")
async def login(credentials: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and returns JWT Bearer token.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user.to_dict(),
    }


@router.get("/me", response_model=UserResponse, summary="Get Authenticated User Profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns profile information for the currently authenticated user.
    """
    return current_user.to_dict()


@router.post("/demo-login", response_model=TokenResponse, summary="1-Click Demo Login for Hackathon Verification")
async def demo_login(demo_req: DemoLoginRequest, db: Session = Depends(get_db)):
    """
    Allows instant 1-click evaluation login for Hackathon evaluators.
    Logs in as either demo citizen or demo administrator.
    """
    target_email = "admin@civiceye.gov" if demo_req.role.lower() == "admin" else "citizen@civiceye.gov"
    user = db.query(User).filter(User.email == target_email).first()
    
    if not user:
        # Fallback create demo user if not present
        role = "admin" if demo_req.role.lower() == "admin" else "citizen"
        name = "Demo Administrator" if role == "admin" else "Demo Citizen"
        user = User(
            email=target_email,
            hashed_password=get_password_hash("Demo@12345"),
            full_name=name,
            phone_number="+91 99999 00000",
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user.to_dict(),
    }
