"""
Orchestration API Schemas - Pydantic models for orchestration endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class OrchestrateRequest(BaseModel):
    """Request schema for orchestration endpoint"""
    event_type: str = Field(..., description="Event type (intent) for routing")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")


class DebugMetadata(BaseModel):
    """Debug metadata returned from orchestration pipeline"""
    intent: Optional[str] = None
    sub_intent: Optional[str] = None
    pathway: Optional[str] = None
    confidence: Optional[float] = None
    fallback_mode: Optional[str] = None
    routing_targets: Optional[List[str]] = None
    policy_flags: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrchestrateResponse(BaseModel):
    """Response schema for orchestration endpoint"""
    routed_agent: str = Field(..., description="Name of routed domain agent")
    result: Dict[str, Any] = Field(default_factory=dict, description="Agent execution result")
    debug: DebugMetadata = Field(..., description="Debug metadata")

    class Config:
        from_attributes = True
