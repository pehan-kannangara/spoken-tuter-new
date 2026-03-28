from pydantic import BaseModel, Field


class OrchestrationRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    role: str = Field(..., description="student | teacher | recruiter | admin | system")
    event_type: str = Field(..., description="Incoming event name")
    payload: dict = Field(default_factory=dict, description="Event payload")


class OrchestrationResponse(BaseModel):
    status: str
    routed_agent: str
    message: str
    debug: dict = Field(default_factory=dict)
