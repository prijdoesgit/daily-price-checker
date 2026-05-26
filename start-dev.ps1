# Local development startup script (Windows PowerShell)
# Prerequisites: Docker Desktop running

Write-Host "Starting MedPrice Intelligence Platform..." -ForegroundColor Cyan

# Check docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Copy env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

# Start services
Write-Host "Starting Docker services..." -ForegroundColor Green
docker-compose up -d postgres redis

Write-Host "Waiting for PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting backend..." -ForegroundColor Green
docker-compose up -d backend celery_worker celery_beat flower

Write-Host "Starting frontend..." -ForegroundColor Green
docker-compose up -d frontend

Write-Host ""
Write-Host "Services started!" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Flower:     http://localhost:5555" -ForegroundColor Cyan
Write-Host ""
Write-Host "View logs: docker-compose logs -f backend" -ForegroundColor Gray
