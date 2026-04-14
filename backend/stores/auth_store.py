"""
Auth Store - User authentication and session management persistence layer
SQLAlchemy ORM models for users and sessions with JWT token handling
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum
import hashlib
import secrets

from passlib.context import CryptContext

# SQLAlchemy declarative base
Base = declarative_base()

# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 parallelization
)


class UserRole(str, enum.Enum):
    """User role enumeration"""
    LEARNER = "learner"
    TEACHER = "teacher"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class User(Base):
    """User model - stores learner/teacher/recruiter/admin profiles"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: secrets.token_hex(18))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.LEARNER)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def set_password(self, plain_password: str):
        """Hash and set password"""
        self.password_hash = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify plain password against hash"""
        return pwd_context.verify(plain_password, self.password_hash)

    def to_dict(self):
        """Serialize user to dict (excluding password_hash)"""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
        }


class Session(Base):
    """Session model - stores JWT tokens and session metadata"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: secrets.token_hex(18))
    user_id = Column(String(36), nullable=False, index=True)
    access_token = Column(String(500), nullable=False, unique=True)
    refresh_token = Column(String(500), nullable=False, unique=True, index=True)
    access_token_expires_at = Column(DateTime, nullable=False, index=True)
    refresh_token_expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def is_access_token_expired(self) -> bool:
        """Check if access token is expired"""
        return datetime.utcnow() >= self.access_token_expires_at

    def is_refresh_token_expired(self) -> bool:
        """Check if refresh token is expired"""
        return datetime.utcnow() >= self.refresh_token_expires_at

    def to_dict(self):
        """Serialize session to dict (excluding tokens for security)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "access_token_expires_at": self.access_token_expires_at.isoformat(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class AuthStore:
    """Auth persistence layer - manages users and sessions"""

    def __init__(self, db_session):
        """Initialize with SQLAlchemy session"""
        self.db = db_session

    def create_user(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.LEARNER,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        """
        Create a new user

        Args:
            email: Unique email address
            password: Plain text password (will be hashed)
            role: User role (learner/teacher/recruiter/admin)
            first_name: Optional first name
            last_name: Optional last name

        Returns:
            User object

        Raises:
            ValueError: If email already exists
        """
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError(f"User with email {email} already exists")

        user = User(
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> User:
        """Retrieve user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str) -> User:
        """Retrieve user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def verify_user_credentials(self, email: str, password: str) -> User:
        """
        Verify email and password

        Returns:
            User object if valid, None otherwise
        """
        user = self.get_user_by_email(email)
        if not user or not user.verify_password(password):
            return None
        return user

    def create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        access_token_expires_in_seconds: int = 3600,  # 1 hour default
        refresh_token_expires_in_seconds: int = 604800,  # 7 days default
        ip_address: str = None,
        user_agent: str = None,
    ) -> Session:
        """
        Create a new session with JWT tokens

        Args:
            user_id: User ID
            access_token: JWT access token
            refresh_token: JWT refresh token
            access_token_expires_in_seconds: TTL for access token
            refresh_token_expires_in_seconds: TTL for refresh token
            ip_address: User IP address
            user_agent: User agent string

        Returns:
            Session object
        """
        now = datetime.utcnow()
        session = Session(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=now + timedelta(seconds=access_token_expires_in_seconds),
            refresh_token_expires_at=now + timedelta(seconds=refresh_token_expires_in_seconds),
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_access_token(self, access_token: str) -> Session:
        """Retrieve active session by access token"""
        session = self.db.query(Session).filter(
            Session.access_token == access_token,
            Session.is_active == True,
        ).first()
        
        if session and session.is_access_token_expired():
            session.is_active = False
            self.db.commit()
            return None
        
        return session

    def get_session_by_refresh_token(self, refresh_token: str) -> Session:
        """Retrieve active session by refresh token"""
        session = self.db.query(Session).filter(
            Session.refresh_token == refresh_token,
            Session.is_active == True,
        ).first()
        
        if session and session.is_refresh_token_expired():
            session.is_active = False
            self.db.commit()
            return None
        
        return session

    def invalidate_session(self, access_token: str):
        """Mark session as inactive (logout)"""
        session = self.db.query(Session).filter(
            Session.access_token == access_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()

    def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        self.db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True,
        ).update({"is_active": False})
        self.db.commit()

    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
