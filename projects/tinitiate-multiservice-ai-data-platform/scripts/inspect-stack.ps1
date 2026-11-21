param(
    [string]$ComposeFile = "tinitiate-ai-onboarding.yml",
    [string]$Service
)

$ErrorActionPreference = "Stop"

Write-Host "=== Docker Engine ===" -ForegroundColor Cyan
docker version
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is unavailable. Start Docker Desktop and retry."
}

Write-Host "`n=== Docker Compose ===" -ForegroundColor Cyan
docker compose version
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose is unavailable."
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}

Write-Host "`n=== Compose configuration validation ===" -ForegroundColor Cyan
docker compose -f $ComposeFile config --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Compose configuration validation failed."
}

Write-Host "`n=== Container status ===" -ForegroundColor Cyan
docker compose -f $ComposeFile ps
if ($LASTEXITCODE -ne 0) {
    throw "Could not read Compose service status."
}

if ($Service) {
    Write-Host "`n=== Recent logs: $Service ===" -ForegroundColor Cyan
    docker compose -f $ComposeFile logs --tail 100 $Service
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read logs for service: $Service"
    }
}

Write-Host "`nInspection completed. Review the status and logs above; this script does not certify service readiness." -ForegroundColor Green
