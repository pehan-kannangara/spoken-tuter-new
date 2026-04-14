"""Database-backed auth and account management for Requirement 3.1."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.core.config import get_session_hours
from backend.db.models import AuthSessionORM, UserAccountORM
from backend.db.session import db_session

LEARNER_ROLES = {"school_student", "university_student", "working_professional"}
VALID_ROLES = LEARNER_ROLES | {"teacher", "recruiter", "administrator", "research_analyst"}
VALID_GOALS = {
    "ielts_exam",
    "general_improvement",
    "for_school",
    "working_purpose",
    "interview_preparation",
    "business_communication",
}
GOAL_TO_PATHWAY = {
    "ielts_exam": "ielts",
    "working_purpose": "ielts",
    "interview_preparation": "ielts",
    "general_improvement": "cefr",
    "for_school": "cefr",
    "business_communication": "business_english",
}


class UserProfile(BaseModel):
    goal: Optional[str] = None
    pathway: Optional[str] = None
    target_band: Optional[float] = None
    target_cefr: Optional[str] = None
    class_code: Optional[str] = None
    business_profile: Optional[dict] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    linked_learner_id: Optional[str] = None


class UserPreferences(BaseModel):
    notifications_enabled: bool = True
    weekly_summary: bool = True
    preferred_timezone: str = "UTC"


class UserAccount(BaseModel):
    user_id: str
    role: str
    name: str
    email: str
    password_hash: str
    password_salt: str
    email_verified: bool = False
    verification_token: Optional[str] = None
    profile: UserProfile = Field(default_factory=UserProfile)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


class AuthSession(BaseModel):
    token: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


def auth_metadata() -> dict:
    return {
        "roles": sorted(VALID_ROLES),
        "learner_roles": sorted(LEARNER_ROLES),
        "goals": sorted(VALID_GOALS),
        "goal_to_pathway": GOAL_TO_PATHWAY,
    }


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()


def _new_verification_token() -> str:
    return secrets.token_urlsafe(24)


def _new_session_token() -> str:
    return secrets.token_urlsafe(32)


def _user_from_orm(row: UserAccountORM) -> UserAccount:
    return UserAccount(
        user_id=row.user_id,
        role=row.role,
        name=row.name,
        email=row.email,
        password_hash=row.password_hash,
        password_salt=row.password_salt,
        email_verified=row.email_verified,
        verification_token=row.verification_token,
        profile=UserProfile(**(row.profile_json or {})),
        preferences=UserPreferences(**(row.preferences_json or {})),
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_login_at=row.last_login_at,
    )


def register_user(
    *,
    role: str,
    name: str,
    email: str,
    password: str,
    goal: Optional[str] = None,
    pathway: Optional[str] = None,
    target_band: Optional[float] = None,
    target_cefr: Optional[str] = None,
    class_code: Optional[str] = None,
    business_profile: Optional[dict] = None,
    organization: Optional[str] = None,
    department: Optional[str] = None,
    title: Optional[str] = None,
) -> tuple[UserAccount, str]:
    role = role.strip().lower()
    email = email.strip().lower()

    if role not in VALID_ROLES:
        raise ValueError("Invalid role.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    profile = UserProfile(
        goal=goal,
        pathway=pathway,
        target_band=target_band,
        target_cefr=target_cefr,
        class_code=class_code,
        business_profile=business_profile,
        organization=organization,
        department=department,
        title=title,
    )

    if role in LEARNER_ROLES:
        if not goal:
            raise ValueError("Learner roles require a goal.")
        if goal not in VALID_GOALS:
            raise ValueError("Invalid goal.")
        inferred_pathway = GOAL_TO_PATHWAY[goal]
        if pathway and pathway != inferred_pathway:
            raise ValueError("Pathway must match selected goal.")
        profile.pathway = inferred_pathway
        if inferred_pathway == "ielts" and target_band is None:
            raise ValueError("IELTS pathway requires target_band.")
        if inferred_pathway in {"cefr", "business_english"} and not target_cefr:
            raise ValueError("CEFR/Business pathway requires target_cefr.")
        if inferred_pathway == "business_english" and not business_profile:
            raise ValueError("Business English pathway requires business_profile.")

    with db_session() as db:
        existing = db.scalar(select(UserAccountORM).where(UserAccountORM.email == email))
        if existing:
            raise ValueError("Email already registered.")

        salt = secrets.token_hex(16)
        token = _new_verification_token()
        row = UserAccountORM(
            user_id=str(uuid.uuid4()),
            role=role,
            name=name,
            email=email,
            password_hash=_hash_password(password, salt),
            password_salt=salt,
            email_verified=False,
            verification_token=token,
            profile_json=profile.model_dump(mode="json"),
            preferences_json=UserPreferences().model_dump(mode="json"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(row)
        db.flush()
        return _user_from_orm(row), token


def verify_email(token: str) -> Optional[UserAccount]:
    with db_session() as db:
        row = db.scalar(select(UserAccountORM).where(UserAccountORM.verification_token == token))
        if not row:
            return None
        row.email_verified = True
        row.verification_token = None
        row.updated_at = datetime.utcnow()
        db.flush()
        return _user_from_orm(row)


def login(email: str, password: str, session_hours: int | None = None) -> tuple[UserAccount, str]:
    email = email.strip().lower()
    duration_hours = session_hours or get_session_hours()

    with db_session() as db:
        row = db.scalar(select(UserAccountORM).where(UserAccountORM.email == email))
        if not row:
            raise ValueError("Invalid credentials.")
        expected = _hash_password(password, row.password_salt)
        if expected != row.password_hash:
            raise ValueError("Invalid credentials.")
        if not row.email_verified:
            raise ValueError("Email not verified.")

        token = _new_session_token()
        db.add(AuthSessionORM(
            token=token,
            user_id=row.user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
        ))
        row.last_login_at = datetime.utcnow()
        row.updated_at = datetime.utcnow()
        db.flush()
        return _user_from_orm(row), token


def get_user_by_session(token: str) -> Optional[UserAccount]:
    with db_session() as db:
        session_row = db.scalar(select(AuthSessionORM).where(AuthSessionORM.token == token))
        if not session_row:
            return None
        if session_row.expires_at < datetime.utcnow():
            db.delete(session_row)
            return None
        row = db.scalar(select(UserAccountORM).where(UserAccountORM.user_id == session_row.user_id))
        if not row:
            return None
        return _user_from_orm(row)


def logout(token: str) -> bool:
    with db_session() as db:
        row = db.scalar(select(AuthSessionORM).where(AuthSessionORM.token == token))
        if not row:
            return False
        db.delete(row)
        return True


def update_profile(
    user_id: str,
    *,
    name: Optional[str] = None,
    preferences: Optional[dict] = None,
    profile_patch: Optional[dict] = None,
) -> Optional[UserAccount]:
    with db_session() as db:
        row = db.scalar(select(UserAccountORM).where(UserAccountORM.user_id == user_id))
        if not row:
            return None
        if name:
            row.name = name
        if preferences:
            merged_prefs = dict(row.preferences_json or {})
            merged_prefs.update(preferences)
            row.preferences_json = UserPreferences(**merged_prefs).model_dump(mode="json")
        if profile_patch:
            merged_profile = dict(row.profile_json or {})
            merged_profile.update(profile_patch)
            row.profile_json = UserProfile(**merged_profile).model_dump(mode="json")
        row.updated_at = datetime.utcnow()
        db.flush()
        return _user_from_orm(row)


def link_learner_profile(user_id: str, learner_id: str) -> None:
    with db_session() as db:
        row = db.scalar(select(UserAccountORM).where(UserAccountORM.user_id == user_id))
        if not row:
            return
        merged_profile = dict(row.profile_json or {})
        merged_profile["linked_learner_id"] = learner_id
        row.profile_json = UserProfile(**merged_profile).model_dump(mode="json")
        row.updated_at = datetime.utcnow()


def public_user(user: UserAccount) -> dict:
    return {
        "user_id": user.user_id,
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "email_verified": user.email_verified,
        "profile": user.profile.model_dump(mode="json"),
        "preferences": user.preferences.model_dump(mode="json"),
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }
