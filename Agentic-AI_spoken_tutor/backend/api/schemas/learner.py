"""Pydantic request/response schemas for learner-facing endpoints."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class BusinessEnglishProfileRequest(BaseModel):
    """Research-aligned profiling fields for Business English learners."""

    industry_sector: str = Field(..., description="IT | finance | healthcare | retail | manufacturing | other")
    job_function: str = Field(..., description="sales | customer_support | operations | management | engineering | other")
    communication_contexts: list[str] = Field(
        default_factory=list,
        description="Typical spoken contexts: meetings, presentations, calls, negotiations, interviews",
    )
    client_facing: bool = Field(False, description="Whether the learner regularly speaks with clients")
    weekly_speaking_hours: int = Field(0, ge=0, le=80, description="Weekly hours of spoken English at work")
    target_use_case: str = Field(
        "meeting_participation",
        description="meeting_participation | presentation_delivery | negotiation | interview_success",
    )
    timeline_weeks: int = Field(12, ge=1, le=104, description="Target improvement timeline in weeks")


class RegisterLearnerRequest(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="school_student | university_student | working_professional")
    pathway: Literal["ielts", "cefr", "business_english"] = Field(..., description="ielts | cefr | business_english")
    goal: str = Field(
        ...,
        description=(
            "ielts_exam | general_improvement | for_school | working_purpose | "
            "interview_preparation | business_communication"
        ),
    )
    target_band: Optional[float] = Field(None, description="Target IELTS band (e.g. 7.0)")
    target_cefr: Optional[str] = Field(None, description="Target CEFR level (e.g. b2)")
    class_code: Optional[str] = Field(None, description="6-char teacher class code")
    business_profile: Optional[BusinessEnglishProfileRequest] = None


class StartSessionRequest(BaseModel):
    learner_id: str = Field(..., description="Learner UUID")
    session_type: str = Field("practice", description="practice | formal_assessment")
    num_questions: int = Field(5, ge=1, le=12, description="Number of questions in this session")
    task_type_filter: Optional[str] = Field(
        None,
        description="Optionally restrict to: part_1 | part_2 | part_3 | cefr_basic | cefr_intermediate | ...",
    )
    level_override: Optional[str] = Field(None, description="Force a specific CEFR/IELTS level filter")


class SubmitResponseRequest(BaseModel):
    transcript: str = Field(..., min_length=3, description="Spoken response text transcript")


class AdvanceSessionRequest(BaseModel):
    pass
