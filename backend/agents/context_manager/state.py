"""
Context Manager State - Data structures for context packaging
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class ActorProfile(BaseModel):
    """Actor/user profile in context"""
    user_id: str
    role: str
    email: Optional[str] = None
    pathway: Optional[str] = None


class WorkflowIntent(BaseModel):
    """Workflow intent information"""
    intent: str
    sub_intent: str
    confidence: float = 0.95


class QualityPolicy(BaseModel):
    """Quality assurance policy"""
    strict_rubric: bool = False
    require_human_review: bool = False
    minimum_quality_score: int = 70


class ScreeningPolicy(BaseModel):
    """Screening/recruitment policy"""
    business_screening_mode: bool = False
    preferred_domains: List[str] = Field(default_factory=list)
    job_level: Optional[str] = None


class ExecutionConstraints(BaseModel):
    """Execution constraints and limits"""
    max_attempts: int = 3
    timeout_seconds: int = 300
    require_approval: bool = False


class ContextPackage(BaseModel):
    """Complete context package passed to domain agents"""
    actor: ActorProfile
    workflow: WorkflowIntent
    quality_policy: QualityPolicy
    screening_policy: ScreeningPolicy
    constraints: ExecutionConstraints
    intent_history: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContextManagerState(BaseModel):
    """State for context manager agent"""
    classifier_state: Dict[str, Any] = Field(..., description="Output from classifier")
    user_context: Dict[str, Any] = Field(..., description="User context from auth")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Original payload")
    
    # Context manager outputs
    context_package: Optional[ContextPackage] = None
    
    class Config:
        from_attributes = True
