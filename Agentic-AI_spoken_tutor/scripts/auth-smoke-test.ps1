param(
  [string]$BaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"

function Assert-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) {
    throw "[auth-smoke] ASSERT FAILED: $Message"
  }
}

Write-Host "[auth-smoke] Base URL: $BaseUrl"

$email = "authflow.user.$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())@example.com"

$registerBody = @{
  role = "working_professional"
  name = "Auth Flow User"
  email = $email
  password = "Pass12345!"
  goal = "business_communication"
  target_cefr = "b2"
  business_profile = @{
    industry_sector = "it"
    job_function = "management"
    communication_contexts = @("meetings", "presentations", "client_calls")
    client_facing = $true
    weekly_speaking_hours = 8
    target_use_case = "presentation_delivery"
    timeline_weeks = 10
  }
}

$register = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/register" -ContentType "application/json" -Body ($registerBody | ConvertTo-Json -Depth 10)
Assert-True ($register.status -eq "ok") "register failed"
Assert-True ($register.user.profile.pathway -eq "business_english") "goal to pathway mapping failed"
$verifyToken = $register.verification_token
Write-Host "[auth-smoke] user registered"

$verify = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/verify-email" -ContentType "application/json" -Body (@{ verification_token = $verifyToken } | ConvertTo-Json)
Assert-True ($verify.status -eq "ok") "verify failed"
Write-Host "[auth-smoke] email verified"

$login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -ContentType "application/json" -Body (@{ email = $email; password = "Pass12345!" } | ConvertTo-Json)
Assert-True ($login.status -eq "ok") "login failed"
$sessionToken = $login.session_token
Assert-True ([string]::IsNullOrWhiteSpace($sessionToken) -eq $false) "session token missing"
Write-Host "[auth-smoke] login ok"

$me = Invoke-RestMethod -Method Get -Uri "$BaseUrl/auth/me" -Headers @{ "x-session-token" = $sessionToken }
Assert-True ($me.status -eq "ok") "me endpoint failed"
Write-Host "[auth-smoke] me endpoint ok"

$update = Invoke-RestMethod -Method Patch -Uri "$BaseUrl/auth/profile" -Headers @{ "x-session-token" = $sessionToken } -ContentType "application/json" -Body (@{ preferences = @{ preferred_timezone = "Asia/Colombo"; weekly_summary = $false } } | ConvertTo-Json)
Assert-True ($update.status -eq "ok") "profile update failed"
Assert-True ($update.user.preferences.preferred_timezone -eq "Asia/Colombo") "profile update did not persist"
Write-Host "[auth-smoke] profile updated"

$logout = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/logout" -Headers @{ "x-session-token" = $sessionToken }
Assert-True ($logout.status -eq "ok") "logout failed"
Write-Host "[auth-smoke] PASS"
