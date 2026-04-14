from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.schemas.orchestration import OrchestrationRequest, OrchestrationResponse
from backend.api.schemas.qa import (
    QAActivateRequest,
    QAGenerateRequest,
    QARetireRequest,
    QAValidateRequest,
)
from backend.api.schemas.learner import (
    RegisterLearnerRequest,
    StartSessionRequest,
    SubmitResponseRequest,
    AdvanceSessionRequest,
)
from backend.api.schemas.auth import (
    LoginRequest,
    RegisterUserRequest,
    UpdateProfileRequest,
    VerifyEmailRequest,
)
from backend.api.schemas.teacher import (
    CreateClassRequest,
    ClassOverviewRequest,
    LearnerDetailRequest,
)
from backend.api.schemas.recruiter import (
    CreateScreeningPackRequest,
    AddCandidateRequest,
    StartCandidateSessionRequest,
)
from backend.agents.qa_workflow.graph import run_qa_workflow
from backend.agents.orchestrator.graph import run_orchestration
from backend.agents.assessment_scoring.graph import run_assessment_scoring
from backend.agents.feedback_pathway.graph import run_feedback_pathway
from backend.agents.recruiter_screening.graph import run_recruiter_screening
from backend.agents.monitoring_analytics.graph import run_monitoring_analytics
from backend.qa_engine.store import get_item, get_lifecycle, list_items, list_active_items
from backend.stores.learner_store import (
    create_learner,
    create_session,
    get_learner,
    get_learner_sessions,
    get_progress,
    get_session,
    advance_session,
    band_to_cefr,
)
from backend.stores.auth_store import (
    LEARNER_ROLES,
    auth_metadata,
    get_user_by_session,
    link_learner_profile,
    login,
    logout,
    public_user,
    register_user,
    update_profile,
    verify_email,
)
from backend.db.bootstrap import init_db
from backend.data.seed_loader import seed_question_bank
import random


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    init_db()
    count = seed_question_bank()
    print(f"[startup] Question bank seeded: {count} items loaded.")
    yield
    # ── Shutdown (nothing to flush for MVP in-memory store) ──────────────


app = FastAPI(
    title="Agentic Spoken Tutor API",
    version="0.2.0",
    description=(
        "FastAPI backend for the AI-powered spoken English tutor platform. "
        "Serves learners, teachers, recruiters, and QA workflows."
    ),
    lifespan=lifespan,
)


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend" / "public"

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get("/")
def frontend_index():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        return {"status": "ok", "message": "Frontend not found. Use /docs for API."}
    return FileResponse(index_file)


@app.get("/meta/pathways")
def pathway_metadata() -> dict:
    """Return supported pathways and profile requirements for frontend forms."""
    return {
        "pathways": ["ielts", "cefr", "business_english"],
        "goals": [
            "ielts_exam",
            "general_improvement",
            "for_school",
            "working_purpose",
            "interview_preparation",
            "business_communication",
        ],
        "pathway_to_goal": {
            "ielts": ["ielts_exam", "working_purpose", "interview_preparation"],
            "cefr": ["general_improvement", "for_school"],
            "business_english": ["business_communication", "working_purpose", "interview_preparation"],
        },
        "business_profile_fields": [
            "industry_sector",
            "job_function",
            "communication_contexts",
            "client_facing",
            "weekly_speaking_hours",
            "target_use_case",
            "timeline_weeks",
        ],
        "research_basis": {
            "cefr_mediation": "Council of Europe CEFR companion volume business communication descriptors",
            "ielts_workplace_transfer": "IELTS speaking rubric dimensions adapted for workplace communication",
            "business_communication": "Workplace English contexts: meetings, presentations, negotiations, client calls",
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ============================================================================
# AUTH + USER MANAGEMENT (Requirement 3.1)
# ============================================================================

@app.get("/auth/meta")
def auth_meta() -> dict:
    return {"status": "ok", **auth_metadata()}


@app.post("/auth/register")
def auth_register(req: RegisterUserRequest) -> dict:
    try:
        user, verification_token = register_user(
            role=req.role,
            name=req.name,
            email=req.email,
            password=req.password,
            goal=req.goal,
            pathway=req.pathway,
            target_band=req.target_band,
            target_cefr=req.target_cefr,
            class_code=req.class_code,
            business_profile=req.business_profile,
            organization=req.organization,
            department=req.department,
            title=req.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if user.role in LEARNER_ROLES:
        learner = create_learner(
            name=user.name,
            email=user.email,
            role=user.role,
            pathway=user.profile.pathway or "cefr",
            goal=user.profile.goal or "general_improvement",
            target_band=user.profile.target_band,
            target_cefr=user.profile.target_cefr,
            class_code=user.profile.class_code,
            business_profile=user.profile.business_profile,
        )
        link_learner_profile(user.user_id, learner.learner_id)

    return {
        "status": "ok",
        "message": "Registration successful. Verify email before login.",
        "user": public_user(user),
        "verification_token": verification_token,
    }


@app.post("/auth/verify-email")
def auth_verify_email(req: VerifyEmailRequest) -> dict:
    user = verify_email(req.verification_token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    return {"status": "ok", "message": "Email verified.", "user": public_user(user)}


@app.post("/auth/login")
def auth_login(req: LoginRequest) -> dict:
    try:
        user, token = login(req.email, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "status": "ok",
        "session_token": token,
        "user": public_user(user),
    }


@app.get("/auth/me")
def auth_me(x_session_token: str | None = Header(default=None)) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing x-session-token header.")
    user = get_user_by_session(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return {"status": "ok", "user": public_user(user)}


@app.patch("/auth/profile")
def auth_update_profile(req: UpdateProfileRequest, x_session_token: str | None = Header(default=None)) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing x-session-token header.")
    user = get_user_by_session(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    updated = update_profile(
        user.user_id,
        name=req.name,
        preferences=req.preferences,
        profile_patch=req.profile_patch,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "ok", "user": public_user(updated)}


@app.post("/auth/logout")
def auth_logout(x_session_token: str | None = Header(default=None)) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing x-session-token header.")
    ok = logout(x_session_token)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return {"status": "ok", "message": "Logged out."}


@app.get("/app/overview")
def app_overview(x_session_token: str | None = Header(default=None)) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing x-session-token header.")
    user = get_user_by_session(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    payload = {
        "status": "ok",
        "user": public_user(user),
        "role_dashboard": None,
    }

    linked_learner_id = user.profile.linked_learner_id
    if user.role in LEARNER_ROLES and linked_learner_id:
        learner = get_learner(linked_learner_id)
        sessions = get_learner_sessions(linked_learner_id)
        progress = get_progress(linked_learner_id)
        payload["role_dashboard"] = {
            "kind": "learner",
            "learner": learner.model_dump() if learner else None,
            "recent_sessions": [s.model_dump() for s in sessions[-5:]],
            "progress": [p.model_dump() for p in progress[-10:]],
        }
    elif user.role == "teacher":
        payload["role_dashboard"] = run_monitoring_analytics(
            user_id=user.user_id,
            payload={"event_type": "get_classes"},
            context={},
        )
    elif user.role == "recruiter":
        payload["role_dashboard"] = run_recruiter_screening(
            user_id=user.user_id,
            payload={"event_type": "list_packs"},
            context={},
        )

    return payload


@app.post("/orchestrate", response_model=OrchestrationResponse)
def orchestrate(req: OrchestrationRequest) -> OrchestrationResponse:
    result = run_orchestration(
        user_id=req.user_id,
        role=req.role,
        event_type=req.event_type,
        payload=req.payload,
    )
    return OrchestrationResponse(**result)


@app.post("/qa/generate")
def qa_generate(req: QAGenerateRequest) -> dict:
    return run_qa_workflow(
        user_id=req.user_id,
        event_type="generate_item",
        payload=req.model_dump(exclude_none=True),
        context={},
    )


@app.post("/qa/validate")
def qa_validate(req: QAValidateRequest) -> dict:
    return run_qa_workflow(
        user_id=req.user_id,
        event_type="validate_item",
        payload=req.model_dump(exclude_none=True),
        context={},
    )


@app.post("/qa/activate")
def qa_activate(req: QAActivateRequest) -> dict:
    return run_qa_workflow(
        user_id=req.user_id,
        event_type="activate_item",
        payload=req.model_dump(exclude_none=True),
        context={},
    )


@app.post("/qa/retire")
def qa_retire(req: QARetireRequest) -> dict:
    return run_qa_workflow(
        user_id=req.user_id,
        event_type="retire_item",
        payload=req.model_dump(exclude_none=True),
        context={},
    )


@app.get("/qa/items")
def qa_list_items() -> dict:
    items = list_items()
    return {
        "count": len(items),
        "items": [item.model_dump() for item in items],
    }


@app.get("/qa/items/{item_id}")
def qa_get_item(item_id: str) -> dict:
    item = get_item(item_id)
    lifecycle = get_lifecycle(item_id)

    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

    return {
        "item": item.model_dump(),
        "lifecycle": lifecycle.model_dump() if lifecycle else None,
    }


# ============================================================================
# LEARNER ENDPOINTS
# ============================================================================

@app.post("/learner/register")
def register_learner(req: RegisterLearnerRequest) -> dict:
    profile = create_learner(
        name=req.name,
        email=req.email,
        role=req.role,
        pathway=req.pathway,
        goal=req.goal,
        target_band=req.target_band,
        target_cefr=req.target_cefr,
        class_code=req.class_code,
        business_profile=req.business_profile.model_dump() if req.business_profile else None,
    )
    return {"status": "ok", "learner": profile.model_dump()}


@app.get("/learner/{learner_id}")
def get_learner_profile(learner_id: str) -> dict:
    profile = get_learner(learner_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Learner not found: {learner_id}")
    return {"status": "ok", "learner": profile.model_dump()}


@app.get("/learner/{learner_id}/progress")
def get_learner_progress(learner_id: str) -> dict:
    return run_feedback_pathway(
        user_id=learner_id,
        payload={"event_type": "get_progress", "learner_id": learner_id},
        context={},
    )


@app.get("/learner/{learner_id}/sessions")
def get_sessions(learner_id: str) -> dict:
    sessions = get_learner_sessions(learner_id)
    return {
        "status": "ok",
        "count": len(sessions),
        "sessions": [s.model_dump() for s in sessions],
    }


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@app.post("/session/start")
def start_session(req: StartSessionRequest) -> dict:
    """Start a practice or formal assessment session for a learner."""
    profile = get_learner(req.learner_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Learner not found: {req.learner_id}")

    # Select questions from active bank
    active_items = list_active_items()
    if not active_items:
        raise HTTPException(status_code=503, detail="No active questions in bank. Seed the question bank first.")

    # Filter by task_type if requested
    pool = active_items
    if req.task_type_filter:
        filtered = [i for i in active_items if str(i.task_type) == req.task_type_filter]
        if filtered:
            pool = filtered

    # Filter by pathway
    pool_by_pathway = [i for i in pool if str(i.pathway) == profile.pathway]
    if pool_by_pathway:
        pool = pool_by_pathway

    # Filter by level_override or current level
    level = req.level_override or profile.current_cefr
    if level and level != "unknown":
        filtered_level = [i for i in pool if str(i.target_level) == level]
        if filtered_level:
            pool = filtered_level

    selected = random.sample(pool, min(req.num_questions, len(pool)))
    question_ids = [q.item_id for q in selected]

    session = create_session(
        learner_id=req.learner_id,
        pathway=profile.pathway,
        session_type=req.session_type,
        question_ids=question_ids,
        band_before=profile.current_band,
    )

    # Return first question immediately
    first_item = get_item(question_ids[0])
    return {
        "status": "ok",
        "session_id": session.session_id,
        "total_questions": len(question_ids),
        "current_index": 0,
        "current_question": first_item.model_dump() if first_item else None,
    }


@app.get("/session/{session_id}")
def get_session_state(session_id: str) -> dict:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return {"status": "ok", "session": session.model_dump()}


@app.get("/session/{session_id}/question")
def get_current_question(session_id: str) -> dict:
    """Return the current (unanswered) question in the session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    if session.status == "completed":
        return {
            "status": "completed",
            "message": "Session is complete. No more questions.",
            "overall_band": session.overall_band,
            "overall_cefr": session.overall_cefr,
        }

    idx = session.current_index
    if idx >= len(session.question_ids):
        return {"status": "completed", "message": "All questions answered."}

    item_id = session.question_ids[idx]
    item = get_item(item_id)
    return {
        "status": "ok",
        "session_id": session_id,
        "question_index": idx,
        "total_questions": len(session.question_ids),
        "question": item.model_dump() if item else None,
    }


@app.post("/session/{session_id}/submit")
def submit_response(session_id: str, req: SubmitResponseRequest) -> dict:
    """Submit a transcript for the current question, receive score + feedback."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    if session.status != "active":
        raise HTTPException(status_code=400, detail=f"Session is not active (status: {session.status}).")

    idx = session.current_index
    if idx >= len(session.question_ids):
        raise HTTPException(status_code=400, detail="All questions already answered.")

    item_id  = session.question_ids[idx]
    item     = get_item(item_id)
    task_type = str(item.task_type) if item else "part_1"

    result = run_assessment_scoring(
        user_id=session.learner_id,
        payload={
            "event_type":     "submit_response",
            "session_id":     session_id,
            "item_id":        item_id,
            "question_index": idx,
            "transcript":     req.transcript,
            "task_type":      task_type,
        },
        context={},
    )
    return result


@app.post("/session/{session_id}/next")
def next_question(session_id: str) -> dict:
    """Advance to the next question after reviewing feedback."""
    session = advance_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    if session.status == "completed":
        return {
            "status": "completed",
            "message": "Session complete!",
            "overall_band": session.overall_band,
            "overall_cefr": session.overall_cefr,
        }

    idx = session.current_index
    item_id = session.question_ids[idx]
    item = get_item(item_id)
    return {
        "status": "ok",
        "question_index": idx,
        "total_questions": len(session.question_ids),
        "question": item.model_dump() if item else None,
    }


@app.get("/session/{session_id}/summary")
def session_summary(session_id: str) -> dict:
    """Return full session summary with per-question scores."""
    return run_feedback_pathway(
        user_id="system",
        payload={"event_type": "get_feedback", "session_id": session_id},
        context={},
    )


# ============================================================================
# TEACHER ENDPOINTS
# ============================================================================

@app.post("/teacher/class/create")
def create_class_endpoint(req: CreateClassRequest) -> dict:
    return run_monitoring_analytics(
        user_id=req.teacher_id,
        payload={"event_type": "create_class", "class_name": req.class_name},
        context={},
    )


@app.get("/teacher/{teacher_id}/classes")
def get_teacher_classes_endpoint(teacher_id: str) -> dict:
    return run_monitoring_analytics(
        user_id=teacher_id,
        payload={"event_type": "get_classes"},
        context={},
    )


@app.get("/teacher/{teacher_id}/class/{class_id}/overview")
def class_overview(teacher_id: str, class_id: str) -> dict:
    return run_monitoring_analytics(
        user_id=teacher_id,
        payload={"event_type": "class_overview", "class_id": class_id},
        context={},
    )


@app.get("/teacher/{teacher_id}/class/{class_id}/risks")
def class_risk_check(teacher_id: str, class_id: str) -> dict:
    return run_monitoring_analytics(
        user_id=teacher_id,
        payload={"event_type": "risk_check", "class_id": class_id},
        context={},
    )


@app.get("/teacher/{teacher_id}/learner/{learner_id}")
def teacher_learner_detail(teacher_id: str, learner_id: str) -> dict:
    return run_monitoring_analytics(
        user_id=teacher_id,
        payload={"event_type": "learner_detail", "learner_id": learner_id},
        context={},
    )


# ============================================================================
# RECRUITER ENDPOINTS
# ============================================================================

@app.post("/recruiter/pack/create")
def create_pack(req: CreateScreeningPackRequest) -> dict:
    return run_recruiter_screening(
        user_id=req.recruiter_id,
        payload={"event_type": "create_screening_pack", **req.model_dump()},
        context={},
    )


@app.get("/recruiter/{recruiter_id}/packs")
def list_recruiter_packs(recruiter_id: str) -> dict:
    return run_recruiter_screening(
        user_id=recruiter_id,
        payload={"event_type": "list_packs"},
        context={},
    )


@app.get("/recruiter/pack/{pack_id}")
def get_pack(pack_id: str) -> dict:
    return run_recruiter_screening(
        user_id="recruiter",
        payload={"event_type": "get_pack", "pack_id": pack_id},
        context={},
    )


@app.post("/recruiter/pack/candidate/add")
def add_candidate(req: AddCandidateRequest) -> dict:
    return run_recruiter_screening(
        user_id="recruiter",
        payload={"event_type": "add_candidate", **req.model_dump()},
        context={},
    )


@app.post("/recruiter/pack/candidate/start-session")
def start_candidate_session(req: StartCandidateSessionRequest) -> dict:
    return run_recruiter_screening(
        user_id=req.learner_id,
        payload={"event_type": "start_candidate_session", **req.model_dump()},
        context={},
    )


@app.get("/recruiter/pack/{pack_id}/results")
def get_pack_results(pack_id: str) -> dict:
    return run_recruiter_screening(
        user_id="recruiter",
        payload={"event_type": "get_pack_results", "pack_id": pack_id},
        context={},
    )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.post("/admin/seed")
def admin_seed(force_reload: bool = False) -> dict:
    """Manually trigger question bank seeding (useful in tests)."""
    count = seed_question_bank(force_reload=force_reload)
    active = list_active_items()
    return {
        "status": "ok",
        "items_seeded": count,
        "total_active_items": len(active),
    }
