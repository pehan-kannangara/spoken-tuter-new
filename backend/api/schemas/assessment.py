"""
Assessment API Schemas - Pydantic models for assessment endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateAssessmentRequest(BaseModel):
    """Request to create new assessment"""
    template_id: str = Field(..., description="Assessment template ID")
    title: str = Field(..., description="Assessment title")
    description: Optional[str] = None
    difficulty_level: Optional[str] = None


class SubmitResponseRequest(BaseModel):
    """Request to submit assessment response"""
    assessment_id: str = Field(..., description="Assessment ID")
    question_id: str = Field(..., description="Question ID")
    response_text: str = Field(..., min_length=1, description="Learner response text")
    response_audio_url: Optional[str] = None


class QualityGateResult(BaseModel):
    """Result of a single quality gate"""
    gate_name: str
    passed: bool
    score_contribution: float


class AssessmentScoreResponse(BaseModel):
    """Response from assessment scoring"""
    status: str
    assessment_id: str
    response_id: Optional[str] = None
    final_score: float = Field(..., ge=0, le=100, description="Score 0-100")
    quality_score: float = Field(..., ge=0, le=100, description="Quality gate score")
    quality_decision: str = Field(..., description="accepted/rejected/requires_review")
    rubric_applied: bool
    gates_passed: List[str] = Field(default_factory=list)
    gates_failed: List[str] = Field(default_factory=list)
    feedback: str = Field(..., description="Human-readable feedback")


class AssessmentResponse(BaseModel):
    """Assessment with results"""
    id: str
    title: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    status: str
    final_score: Optional[float] = None
    quality_decision: Optional[str] = None
    rubric_applied: bool
    created_at: datetime
    completed_at: Optional[datetime] = None


class LearnerAssessmentHistory(BaseModel):
    """Assessment history for learner"""
    total_assessments: int
    completed_assessments: int
    average_score: float
    recent_assessments: List[AssessmentResponse]
