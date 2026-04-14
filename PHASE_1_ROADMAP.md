# Phase 1 Implementation Roadmap - Spoken Tutor

**Timeline:** 4 weeks (20 working days)  
**Scope:** Core MVP loop: Auth → Learner Onboarding → Assessment → Scoring → Recruiter Screening  
**Tech Stack:** FastAPI, SQLAlchemy (SQLite/PostGres-ready), Pydantic, Responsive Vanilla JS  
**Go-Live Goal:** Phase 1 MVP (4 agents + 3 orchestration components fully functional)

---

## Week 1: Auth & Session Foundation
**Goal:** Secure user authentication and session persistence layer  
**Deliverables:**

### Backend (3 days)
- [ ] **1.1** Implement JWT token generation & validation in `backend/api/main.py`
  - `POST /auth/signup` - Register learner/teacher/recruiter
  - `POST /auth/login` - Issue JWT token + refresh token
  - `POST /auth/refresh` - Extend session
  - `GET /auth/verify` - Validate token
  - Middleware: Add JWT auth check to all protected endpoints

- [ ] **1.2** Create `backend/stores/auth_store.py`
  - User model (id, email, password_hash, role, created_at, last_login)
  - Session model (user_id, token, refresh_token, expires_at)
  - Hashing: Use `passlib.bcrypt` for passwords
  - Methods: `create_user()`, `verify_password()`, `issue_token()`, `validate_token()`

- [ ] **1.3** Build auth endpoints in `backend/api/main.py`
  - Input validation via Pydantic schemas in `backend/api/schemas/auth.py`
  - Response contracts: `{"access_token": "...", "user": {...}, "expires_in": 3600}`
  - Error handling: 401 Unauthorized, 409 Conflict (email exists)

### Frontend (2 days)
- [ ] **1.4** Add auth forms to `frontend/public/index.html`
  - Login form (email, password, submit button)
  - Signup form (email, password, confirm, role selector, submit button)
  - Auth toggle: Show/hide based on token in localStorage
  - On success: Store token + user profile in localStorage

- [ ] **1.5** Implement auth event listeners
  - `#login-form submit` → POST /auth/login + store token
  - `#signup-form submit` → POST /auth/signup + auto-login redirect
  - `#logout-btn click` → Clear localStorage + show login form
  - On page load: Check token validity, auto-redirect if expired

### Database
- [ ] **1.6** Create migration: `migrations/001_init_auth_schema.sql`
  - users table
  - sessions table
  - Indexes on email, token, expires_at

**Test Smoke:** `/auth/login` returns valid JWT; token rejects expired requests

---

## Week 2: Assessment Scoring & Rubric Enforcement
**Goal:** Functional assessment_scoring domain agent + quality gate enforcement  
**Deliverables:**

### Backend Assessment Agent (3 days)
- [ ] **2.1** Expand `backend/agents/assessment_scoring/graph.py`
  - `run_assessment()` - Main orchestration function
  - `_load_assessment_template()` - Fetch from question_bank
  - `_score_response()` - Call LLM or rubric engine for scoring
  - `_aggregate_scores()` - Combine sub-scores to overall assessment score (0-100)
  - `_transition_lifecycle()` - Mark assessment as completed
  - Inputs: `context`, `payload` (assessment_id, candidate_response)
  - Outputs: `assessment_result` (score, feedback, recommended_next_action)

- [ ] **2.2** Add QA rubric enforcement hook
  - `_apply_quality_rubric()` - Use context.quality_policy.strict_rubric
  - If strict_rubric=true: minimum_quality_score=85 (else 70)
  - If score < threshold: Trigger human review workflow or auto-reject
  - Log rubric decision in assessment result

- [ ] **2.3** Implement scoring endpoint in `backend/api/main.py`
  - `POST /assessment/score` - Submit response + get score
  - `GET /assessment/{id}/results` - Retrieve assessment with scores
  - Request validation: Pydantic schema in `backend/api/schemas/assessment.py`
  - Response: `{"assessment_id": "...", "score": 85, "feedback": "...", "quality_decision": "accepted"}`

### Database
- [ ] **2.4** Create migration: `migrations/002_assessment_schema.sql`
  - assessments table (id, learner_id, template_id, status, created_at)
  - assessment_responses table (id, assessment_id, response_text, score, rubric_applied)
  - Indexes on learner_id, status

### Frontend Assessment Flow (2 days)
- [ ] **2.5** Build assessment display UI
  - Load assessment template from `/assessment/{id}` endpoint
  - Display question(s), input textarea for response
  - Submit button → POST /assessment/score
  - Show live score + feedback after submission
  - Preserve in localStorage for session resume

- [ ] **2.6** Add assessment event listeners
  - `#assessment-form submit` → Collect response + POST /assessment/score
  - Handle rubric decision (accepted → highlight success; rejected → show reason)
  - Auto-navigate to next assessment or dashboard on completion

**Test Smoke:** `/assessment/score` returns numeric score 0-100; rubric enforcement triggers at strict_rubric=true

---

## Week 3: Teacher Class Management & Learner Progress
**Goal:** Teachers can create classes, assign learners, view progress dashboards  
**Deliverables:**

### Backend Teacher Agent (3 days)
- [ ] **3.1** Expand `backend/agents/feedback_pathway/graph.py`
  - `run_class_management()` - Create/read/update/delete classes
  - `run_learner_assignment()` - Add/remove learners from class
  - `run_progress_aggregation()` - Fetch all learner assessment scores in class
  - `run_generate_feedback()` - LLM-based feedback from assessment results
  - Inputs: `context`, `payload` (class_name, learner_ids, date_range for progress)
  - Outputs: `class_result`, `progress_board` (learner_id → [assessment_scores, trend, recommended_action])

- [ ] **3.2** Add teacher endpoints in `backend/api/main.py`
  - `POST /teacher/class` - Create class (name, description)
  - `GET /teacher/class/{id}` - Fetch class with learner list
  - `POST /teacher/class/{id}/learners` - Add learners to class
  - `DELETE /teacher/class/{id}/learners/{student_id}` - Remove learner
  - `GET /teacher/class/{id}/progress` - Aggregate learner scores + trends
  - `POST /teacher/feedback/{assessment_id}` - Generate teacher feedback
  - Pydantic schemas in `backend/api/schemas/teacher.py`

- [ ] **3.3** Create `backend/stores/class_store.py`
  - Class model (id, teacher_id, name, description, created_at, learner_ids)
  - Methods: `create_class()`, `add_learner()`, `get_progress_board()`, `get_learner_trend()`

### Frontend Teacher Dashboard (2 days)
- [ ] **3.4** Build teacher dashboard UI
  - Class list card (create new class button)
  - Class detail view (learner roster, progress board with sortable columns)
  - Progress board columns: Learner Name | Latest Score | Trend (↑/→/↓) | Status | Actions
  - Learner detail modal: Show individual assessment history, feedback

- [ ] **3.5** Add teacher event listeners
  - `#create-class-btn click` → Modal form → POST /teacher/class
  - `#add-learner-btn click` → Search/select learner → POST /teacher/class/{id}/learners
  - `#learner-row click` → Load learner modal with full history
  - Auto-refresh progress board every 30 seconds (poll /teacher/class/{id}/progress)

### Database
- [ ] **3.6** Create migration: `migrations/003_teacher_schema.sql`
  - classes table (id, teacher_id, name, description, created_at)
  - class_learners junction table (class_id, learner_id)
  - Indexes on teacher_id, created_at

**Test Smoke:** `/teacher/class` creates class; `/teacher/class/{id}/progress` returns learner board with scores

---

## Week 4: Recruiter Screening End-to-End & MVP Closure
**Goal:** Recruiter screening flow fully operational + smoke test suite  
**Deliverables:**

### Backend Recruiter Screening (2 days)
- [ ] **4.1** Complete `recruiter_screening` agent endpoints in `backend/api/main.py`
  - `POST /recruiter/pack` - Create screening pack (role_name, job_level, min_band, candidate_ids)
  - `GET /recruiter/pack/{id}` - Fetch pack with candidates + progress
  - `POST /recruiter/pack/{id}/start-session` - Begin screening for a candidate
  - `POST /recruiter/pack/{id}/submit-response` - Record candidate response + score
  - `GET /recruiter/pack/{id}/results` - Results board (all candidates, all questions, final scores)
  - `GET /recruiter/pack/{id}/export` - Export results as CSV
  - Pydantic schemas in `backend/api/schemas/recruiter.py`

- [ ] **4.2** Integrate business English task selection
  - `_select_screening_questions()` already filters by pathway + job_level
  - Validate that senior-level recruiter screening gets presentation/negotiation/leadership tasks
  - Add fallback to IELTS tasks if insufficient business English questions

### Frontend Recruiter Workflow (1 day)
- [ ] **4.3** Build recruiter screening UI
  - Screening pack creation form (role name, job level dropdown, candidate CSV upload)
  - Candidate session view (load 1st question, collect response, next/submit buttons)
  - Results board (candidate_name | final_score | status | download button)

- [ ] **4.4** Add recruiter event listeners
  - `#create-pack-btn click` → Form → POST /recruiter/pack
  - `#start-session-btn click` → POST /recruiter/pack/{id}/start-session + load 1st question
  - `#next-question-btn click` → POST /recruiter/pack/{id}/submit-response + load next question
  - `#export-results-btn click` → Fetch /recruiter/pack/{id}/export + download CSV

### Database
- [ ] **4.5** Create migration: `migrations/004_recruiter_schema.sql`
  - screening_packs table (id, recruiter_id, role_name, job_level, min_band, created_at)
  - pack_candidates table (pack_id, candidate_id, status, final_score)
  - screening_sessions table (id, pack_id, candidate_id, question_index, response_text, score)

### Smoke Test Suite (1 day)
- [ ] **4.6** Create `backend/tests/test_phase1_smoke.py`
  - Test auth flow: signup → login → token refresh
  - Test assessment: load assessment → submit response → get score
  - Test teacher: create class → add learner → get progress
  - Test recruiter: create pack → start session → submit response → get results
  - Run all tests: `pytest backend/tests/test_phase1_smoke.py -v`

- [ ] **4.7** Create `frontend/tests/test_e2e_phase1.html`
  - Manual E2E checklist: Can you complete all 4 major flows in UI?
  - Document test results + any blockers

### Go-Live Deployment
- [ ] **4.8** Final validation
  - All endpoints return 200 OK
  - All localStorage persistence works
  - API & Frontend errors are user-friendly (no 500 uncaught exceptions)
  - Phase 1 MVP declaration: Ready for stakeholder review

**Test Smoke:** Complete recruiter screening flow end-to-end; export results CSV

---

## Summary: Phase 1 MVP Scope

| Component | Status | Owner | Confidence |
|-----------|--------|-------|------------|
| Auth & Sessions | Week 1 | Backend API | High |
| Assessments & Scoring | Week 2 | assessment_scoring agent | High |
| Teacher Class Mgmt | Week 3 | feedback_pathway agent | High |
| Recruiter Screening | Week 4 | recruiter_screening agent | Medium (depends on business Q selection) |
| QA Validation Gate | Week 2 | qa_workflow + governance | High |
| Responsive Frontend | Weeks 1-4 | Frontend Team | High |
| Database Persistence | Ongoing | SQLAlchemy ORM | High |

---

## Success Criteria (Phase 1 Definition of Done)

✅ All 4 domain agents operational with debug output  
✅ All required API endpoints return valid JSON responses  
✅ JWT auth persists learner/teacher/recruiter sessions  
✅ Assessment scoring enforces rubric policies (strict_rubric gate)  
✅ Recruiter screening selects business English tasks by job level  
✅ Teacher dashboard aggregates learner progress  
✅ Frontend UI responsive on mobile/tablet/desktop  
✅ Smoke test suite runs green (all major flows tested)  
✅ Zero unhandled 500 errors in test coverage  

---

## Next Steps Post-Phase 1

**Phase 2 (Weeks 5-8):** 
- Advanced teacher analytics (cohort comparisons, mastery tracking)
- Candidate performance deep-dives (item difficulty, discrimination)
- LLM-based feedback loop (auto-generate targeted recommendations)
- Data export/reporting for stakeholders

**Phase 3 (Weeks 9-12):**
- Docker containerization + CI/CD pipeline
- PostgreSQL migration + production secrets
- API rate limiting + request validation hardening
- Performance optimization (caching, database indexing)

---

**Phase 1 Start Date:** Today  
**Phase 1 Target Completion:** Week of [TODAY + 20 working days]  
**Success Milestone:** MVP stakeholder demo with all 4 user personas (learner, teacher, recruiter, admin)

