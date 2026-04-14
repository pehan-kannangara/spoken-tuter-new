"""Pydantic schemas for Requirement 3.1 auth and account management."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RegisterUserRequest(BaseModel):
    role: Literal[
        "school_student",
        "university_student",
        "working_professional",
        "teacher",
        "recruiter",
        "administrator",
        "research_analyst",
    ]
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=200)

    goal: Optional[str] = None
    pathway: Optional[Literal["ielts", "cefr", "business_english"]] = None
    target_band: Optional[float] = Field(None, ge=1.0, le=9.0)
    target_cefr: Optional[Literal["a1", "a2", "b1", "b2", "c1", "c2"]] = None
    class_code: Optional[str] = None
    business_profile: Optional[dict[str, Any]] = None

    organization: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class VerifyEmailRequest(BaseModel):
    verification_token: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None
    profile_patch: Optional[dict[str, Any]] = None
