"""
Authentication routes for user registration and login.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, Token
from auth_utils import Hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **name**: User's full name
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **role**: User role (Admin or User, defaults to User)
    """
    # Log incoming registration request
    print(f"[REGISTER] Registration attempt: {user_data.email} ({user_data.name})")
    
    # Sanitize inputs
    email = user_data.email.strip().lower()
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = Hash.hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hashed_password,
        role=user_data.role,
        avatar=user_data.avatar
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        # Check for integrity error (duplicate entry)
        if "unique constraint" in str(e).lower():
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user. Please try again."
        )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login.
    
    - **username**: User's email address (OAuth2 spec uses 'username' field)
    - **password**: User's password
    
    Returns a JWT access token that expires in 30 minutes.
    """
    # OAuth2 spec uses 'username' field, but we use email
    email = form_data.username
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not Hash.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
