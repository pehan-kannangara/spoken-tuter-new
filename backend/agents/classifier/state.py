"""
Classifier Agent State - Data structures for classification pipeline
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class ClassifierState(BaseModel):
    """State for classifier agent"""
    event_type: str = Field(..., description="Type of event/intent")
    user_id: str = Field(..., description="User ID")
    user_role: str = Field(..., description="User role (learner/teacher/recruiter/admin)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    
    # Classifier outputs
    intent: Optional[str] = None
    sub_intent: Optional[str] = None
    pathway: Optional[str] = None
    confidence: Optional[float] = None
    fallback_mode: Optional[str] = None
    routing_targets: Optional[List[str]] = None
    policy_flags: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
