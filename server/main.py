"""
FastAPI application entry point for the insurance backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_db
from models import User
from dependencies import get_current_user
from routers import auth as auth_router
from routers import claims as claims_router
from routers import ai as ai_router
from routers import policies as policies_router
from routers import documents as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    await init_db()
    print("[OK] Database initialized successfully")
    yield
    # Shutdown: cleanup if needed
    print("[BYE] Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title="Vantage Insurance API",
    description="Backend API for insurance claim management and fraud detection",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500"
    ],  # Vite/React dev servers + Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(claims_router.router, prefix="/claims", tags=["Claims"])
app.include_router(ai_router.router, prefix="/ai", tags=["AI"])
app.include_router(policies_router.router, tags=["Policies"])
app.include_router(documents_router.router, prefix="/documents", tags=["Documents / Knowledge Bridge"])



@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Vantage Insurance API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    from schemas import UserResponse
    return UserResponse.model_validate(current_user)


@app.patch("/me")
async def update_current_user_info(
    user_update: dict = Body(...), # Using dict to avoid importing schema at top level if circular dep risk
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current authenticated user information.
    """
    from schemas import UserResponse, UserUpdate
    
    # Validate with schema
    update_data = UserUpdate(**user_update)
    
    # Update fields
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.email is not None:
        current_user.email = update_data.email
    if update_data.avatar is not None:
        current_user.avatar = update_data.avatar
    if update_data.notifications_enabled is not None:
        current_user.notifications_enabled = update_data.notifications_enabled

    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
