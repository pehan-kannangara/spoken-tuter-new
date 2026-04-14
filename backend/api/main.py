"""
Spoken Tutor API - FastAPI application entry point
Orchestrates all backend services: auth, assessment, teaching, recruiting, QA
"""

import os
import sys
import json
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession

# Import schemas
from .schemas.auth import (
    SignupRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, SimpleTokenResponse, VerifyTokenResponse, ErrorResponse, UserResponse
)
from .schemas.orchestration import (
    OrchestrateRequest, OrchestrateResponse, DebugMetadata
)

# Import stores
from ..stores.auth_store import AuthStore, User, UserRole, Base as AuthBase
from ..stores.assessment_store import AssessmentStore, Base as AssessmentBase

# Import orchestration components
from ..agents.orchestrator.graph import run_orchestration

# ============================================================================
# CONFIG & SETUP
# ============================================================================

# Environment & paths
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spoken_tutor.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Frontend path
BACKEND_DIR = Path(__file__).parent.parent.parent
FRONTEND_DIR = BACKEND_DIR / "frontend" / "public"

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
AuthBase.metadata.create_all(bind=engine)
AssessmentBase.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Spoken Tutor API",
    description="Agentic AI Spoken Language Tutoring Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - serve frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ============================================================================
# JWT UTILITIES
# ============================================================================

def create_jwt_token(
    data: Dict[str, Any],
    expires_in_seconds: int = None
) -> tuple[str, datetime]:
    """
    Create a JWT token with optional expiration

    Args:
        data: Claims to encode in token
        expires_in_seconds: Token TTL (default: ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    if expires_in_seconds is None:
        expires_in_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt, expire


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_db():
    """Dependency: Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> User:
    """
    Dependency: Get current authenticated user from JWT token

    Args:
        authorization: Bearer token from Authorization header
        db: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    payload = verify_jwt_token(token)
    user_id = payload.get("sub")

    auth_store = AuthStore(db)
    user = auth_store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/auth/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: DBSession = Depends(get_db)):
    """
    Register a new user account

    Args:
        request: Signup request with email, password, role

    Returns:
        TokenResponse with access_token, refresh_token, user data

    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        auth_store = AuthStore(db)

        # Create user
        user = auth_store.create_user(
            email=request.email,
            password=request.password,
            role=UserRole(request.role),
            first_name=request.first_name,
            last_name=request.last_name,
        )

        # Create tokens
        access_token, access_exp = create_jwt_token(
            {"sub": user.id, "email": user.email, "role": user.role.value},
            expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        refresh_token, refresh_exp = create_jwt_token(
            {"sub": user.id, "type": "refresh"},
            expires_in_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        # Create session
        auth_store.create_session(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token_expires_in_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        # Update last login
        auth_store.update_last_login(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user.to_dict())
        )

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DBSession = Depends(get_db)):
    """
    Authenticate user with email and password

    Args:
        request: Login request with email and password

    Returns:
        TokenResponse with access_token, refresh_token, user data

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        auth_store = AuthStore(db)

        # Verify credentials
        user = auth_store.verify_user_credentials(request.email, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create tokens
        access_token, access_exp = create_jwt_token(
            {"sub": user.id, "email": user.email, "role": user.role.value},
            expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        refresh_token, refresh_exp = create_jwt_token(
            {"sub": user.id, "type": "refresh"},
            expires_in_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        # Create session
        auth_store.create_session(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token_expires_in_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        # Update last login
        auth_store.update_last_login(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user.to_dict())
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/auth/refresh", response_model=SimpleTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DBSession = Depends(get_db)
):
    """
    Refresh expired access token using refresh token

    Args:
        request: RefreshTokenRequest with refresh_token

    Returns:
        SimpleTokenResponse with new access_token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        auth_store = AuthStore(db)

        # Validate refresh token
        verify_jwt_token(request.refresh_token)

        # Get session
        session = auth_store.get_session_by_refresh_token(request.refresh_token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Get user
        user = auth_store.get_user_by_id(session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Create new access token
        access_token, access_exp = create_jwt_token(
            {"sub": user.id, "email": user.email, "role": user.role.value},
            expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        # Invalidate old session, create new one with new tokens
        auth_store.invalidate_session(session.access_token)
        new_session = auth_store.create_session(
            user_id=user.id,
            access_token=access_token,
            refresh_token=request.refresh_token,
            access_token_expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token_expires_in_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return SimpleTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Refresh token error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/auth/verify", response_model=VerifyTokenResponse)
async def verify(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Verify current JWT token validity

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        VerifyTokenResponse with validity status and user info

    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not authorization:
        return VerifyTokenResponse(valid=False)

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return VerifyTokenResponse(valid=False)
    except ValueError:
        return VerifyTokenResponse(valid=False)

    try:
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")
        
        auth_store = AuthStore(db)
        user = auth_store.get_user_by_id(user_id)
        
        if not user:
            return VerifyTokenResponse(valid=False)

        exp_time = datetime.fromtimestamp(payload.get("exp"))
        
        return VerifyTokenResponse(
            valid=True,
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            expires_at=exp_time.isoformat()
        )
    except HTTPException:
        return VerifyTokenResponse(valid=False)


@app.post("/auth/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Logout user by invalidating their session

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        {"message": "Logged out successfully"}
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    try:
        auth_store = AuthStore(db)
        auth_store.invalidate_session(token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        print(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ORCHESTRATION ENDPOINTS
# ============================================================================

@app.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main orchestration endpoint - routes requests to appropriate domain agent

    Args:
        request: OrchestrateRequest with event_type, payload
        current_user: Authenticated user from JWT

    Returns:
        OrchestrateResponse with routed_agent, result, debug metadata
    """
    try:
        # Run orchestration pipeline: classifier → context_manager → domain agent
        result = await run_orchestration(
            event_type=request.event_type,
            payload=request.payload,
            user_context={
                "user_id": current_user.id,
                "email": current_user.email,
                "role": current_user.role.value,
            },
            db=db
        )

        return OrchestrateResponse(
            routed_agent=result.get("routed_agent", "unknown"),
            result=result.get("result", {}),
            debug=DebugMetadata(**result.get("debug", {}))
        )

    except Exception as e:
        print(f"Orchestration error: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


# ============================================================================
# ASSESSMENT ENDPOINTS
# ============================================================================

from .schemas.assessment import (
    CreateAssessmentRequest, SubmitResponseRequest,
    AssessmentScoreResponse, AssessmentResponse, LearnerAssessmentHistory
)
from ..stores.assessment_store import AssessmentStore, Assessment as AssessmentModel
from ..agents.assessment_scoring.graph import run_assessment_scoring


@app.post("/assessment/create", response_model=AssessmentResponse)
async def create_assessment(
    request: CreateAssessmentRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new assessment for learner
    
    Args:
        request: CreateAssessmentRequest
        current_user: Authenticated user
        
    Returns:
        AssessmentResponse with assessment details
    """
    try:
        assessment_store = AssessmentStore(db)
        
        assessment = assessment_store.create_assessment(
            learner_id=current_user.id,
            template_id=request.template_id,
            title=request.title,
            description=request.description,
            difficulty_level=request.difficulty_level,
        )
        
        return AssessmentResponse(
            id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            difficulty_level=assessment.difficulty_level,
            status=assessment.status,
            final_score=assessment.final_score,
            quality_decision=assessment.quality_decision,
            rubric_applied=assessment.rubric_applied,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
        )
        
    except Exception as e:
        print(f"Create assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assessment/score", response_model=AssessmentScoreResponse)
async def score_assessment(
    request: SubmitResponseRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit assessment response and get scoring
    
    Args:
        request: SubmitResponseRequest with response text
        current_user: Authenticated user
        
    Returns:
        AssessmentScoreResponse with score and quality decision
    """
    try:
        assessment_store = AssessmentStore(db)
        
        # Get assessment
        assessment = assessment_store.get_assessment(request.assessment_id)
        if not assessment or assessment.learner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Record response
        response = assessment_store.create_response(
            assessment_id=request.assessment_id,
            question_id=request.question_id,
            response_text=request.response_text,
            response_audio_url=request.response_audio_url,
        )
        
        # Build context for scoring
        context_package = {
            "actor": {"user_id": current_user.id, "role": current_user.role.value},
            "workflow": {"intent": "score_assessment"},
            "quality_policy": {
                "strict_rubric": current_user.role.value == "recruiter",
                "minimum_quality_score": 70,
            },
            "screening_policy": {},
        }
        
        # Score assessment
        payload = {
            "assessment_id": request.assessment_id,
            "response_id": response.id,
            "question_id": request.question_id,
            "response_text": request.response_text,
            "learner_id": current_user.id,
        }
        
        result = await run_assessment_scoring(
            context_package=context_package,
            payload=payload,
            db=db,
        )
        
        return AssessmentScoreResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Score assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessment/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assessment details and results
    
    Args:
        assessment_id: Assessment ID
        current_user: Authenticated user
        
    Returns:
        AssessmentResponse with details
    """
    try:
        assessment_store = AssessmentStore(db)
        assessment = assessment_store.get_assessment(assessment_id)
        
        if not assessment or assessment.learner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        return AssessmentResponse(
            id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            difficulty_level=assessment.difficulty_level,
            status=assessment.status,
            final_score=assessment.final_score,
            quality_decision=assessment.quality_decision,
            rubric_applied=assessment.rubric_applied,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessment/history/all", response_model=LearnerAssessmentHistory)
async def get_assessment_history(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assessment history for current learner
    
    Args:
        current_user: Authenticated user
        
    Returns:
        LearnerAssessmentHistory with stats and recent assessments
    """
    try:
        assessment_store = AssessmentStore(db)
        assessments = assessment_store.get_learner_assessments(current_user.id)
        
        # Calculate stats
        completed = [a for a in assessments if a.status == "completed"]
        total_assessments = len(assessments)
        completed_assessments = len(completed)
        
        # Calculate average score
        scores = [a.final_score for a in completed if a.final_score]
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # Recent assessments (limit to 5)
        recent = assessments[:5]
        
        return LearnerAssessmentHistory(
            total_assessments=total_assessments,
            completed_assessments=completed_assessments,
            average_score=average_score,
            recent_assessments=[
                AssessmentResponse(
                    id=a.id,
                    title=a.title,
                    description=a.description,
                    difficulty_level=a.difficulty_level,
                    status=a.status,
                    final_score=a.final_score,
                    quality_decision=a.quality_decision,
                    rubric_applied=a.rubric_applied,
                    created_at=a.created_at,
                    completed_at=a.completed_at,
                )
                for a in recent
            ],
        )
        
    except Exception as e:
        print(f"Get assessment history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Serve frontend index.html"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    else:
        return {"message": "Welcome to Spoken Tutor API. Frontend not configured."}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if DEBUG else "An error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        },
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on application startup"""
    print("🚀 Spoken Tutor API starting...")
    print(f"📊 Database: {DATABASE_URL}")
    print(f"🎯 Frontend: {FRONTEND_DIR}")
    print(f"🔐 JWT Algorithm: {JWT_ALGORITHM}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("🛑 Spoken Tutor API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=DEBUG,
        log_level="info"
    )
