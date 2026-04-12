param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw "Smoke test failed: $Message"
    }
}

Write-Host "[smoke] Base URL: $BaseUrl"

# 1) Health
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
Assert-True ($health.status -eq "ok") "Health endpoint did not return status=ok"
Write-Host "[smoke] health ok"

# 2) Register learner
$nonce = [guid]::NewGuid().ToString().Substring(0, 8)
$registerPayload = @{
    name = "Smoke User"
    email = "smoke-$nonce@test.local"
    role = "university_student"
    pathway = "ielts"
    goal = "ielts_exam"
} | ConvertTo-Json

$reg = Invoke-RestMethod -Uri "$BaseUrl/learner/register" -Method Post -ContentType "application/json" -Body $registerPayload
Assert-True ($reg.status -eq "ok") "Learner register did not return status=ok"
$learnerId = $reg.learner.learner_id
Assert-True (-not [string]::IsNullOrWhiteSpace($learnerId)) "Learner ID missing"
Write-Host "[smoke] learner created: $learnerId"

# 3) Start session
$startPayload = @{
    learner_id = $learnerId
    session_type = "practice"
    num_questions = 2
} | ConvertTo-Json

$sessionStart = Invoke-RestMethod -Uri "$BaseUrl/session/start" -Method Post -ContentType "application/json" -Body $startPayload
Assert-True ($sessionStart.status -eq "ok") "Session start did not return status=ok"
$sessionId = $sessionStart.session_id
Assert-True (-not [string]::IsNullOrWhiteSpace($sessionId)) "Session ID missing"
Write-Host "[smoke] session created: $sessionId"

# 4) Submit first answer
$submitPayload = @{
    transcript = "I enjoy studying English because it improves my confidence and communication. I practice daily by speaking about familiar topics, and I try to use clear structure in my answers."
} | ConvertTo-Json

$submit = Invoke-RestMethod -Uri "$BaseUrl/session/$sessionId/submit" -Method Post -ContentType "application/json" -Body $submitPayload
Assert-True ($submit.status -eq "ok") "Submit response did not return status=ok"
Assert-True ($null -ne $submit.score.overall_band) "Score overall_band missing"
Assert-True ($null -ne $submit.feedback) "Feedback payload missing"
Write-Host "[smoke] submit scored: band=$($submit.score.overall_band) cefr=$($submit.score.cefr_level)"

# 5) Teacher create class
$teacherPayload = @{
    teacher_id = "teacher-smoke"
    class_name = "Smoke Batch"
} | ConvertTo-Json

$teacher = Invoke-RestMethod -Uri "$BaseUrl/teacher/class/create" -Method Post -ContentType "application/json" -Body $teacherPayload
Assert-True ($teacher.status -eq "ok") "Teacher class create did not return status=ok"
Write-Host "[smoke] class created: $($teacher.class_id)"

# 6) Recruiter create pack
$recruiterPayload = @{
    recruiter_id = "recruiter-smoke"
    role_name = "QA Engineer"
    department = "Engineering"
    min_band = 6.0
} | ConvertTo-Json

$pack = Invoke-RestMethod -Uri "$BaseUrl/recruiter/pack/create" -Method Post -ContentType "application/json" -Body $recruiterPayload
Assert-True ($pack.status -eq "ok") "Recruiter pack create did not return status=ok"
Write-Host "[smoke] pack created: $($pack.pack_id)"

Write-Host "[smoke] PASS"
