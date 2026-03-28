from fastapi import FastAPI

from backend.api.schemas.orchestration import OrchestrationRequest, OrchestrationResponse
from backend.agents.orchestrator.graph import run_orchestration

app = FastAPI(
    title="Agentic Spoken Tutor API",
    version="0.1.0",
    description="FastAPI backend for agentic orchestration and domain workflows",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrationResponse)
def orchestrate(req: OrchestrationRequest) -> OrchestrationResponse:
    result = run_orchestration(
        user_id=req.user_id,
        role=req.role,
        event_type=req.event_type,
        payload=req.payload,
    )
    return OrchestrationResponse(**result)
