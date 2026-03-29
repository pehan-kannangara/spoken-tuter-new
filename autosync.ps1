param(
    [string]$Message = "auto update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

$ErrorActionPreference = "Stop"

# Ensure we are in a git repository.
git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not inside a git repository."
    exit 1
}

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $branch) {
    Write-Error "Could not detect current branch."
    exit 1
}

# Stage all changes.
git add -A

# Commit only when there are staged changes.
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m $Message
} else {
    Write-Host "No local changes to commit."
}

# Keep local branch up to date before pushing.
Write-Host "Pulling latest changes from origin/$branch..."
git pull --rebase origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pull --rebase failed. Resolve conflicts, then run again."
    exit 1
}

Write-Host "Pushing to origin/$branch..."
git push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Error "Push failed. Check permissions/authentication and try again."
    exit 1
}

Write-Host "Repository synced successfully on branch '$branch'."
