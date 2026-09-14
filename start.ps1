# SENTINEL Quick Start Script
# This script starts the application with Docker Compose

Write-Host "🚀 Starting SENTINEL Application..." -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating default .env..." -ForegroundColor Yellow
    @"
JWT_SECRET=dev-secret-change-in-production
SENTINEL_APP_ENV=development
SENTINEL_LOG_LEVEL=INFO
SENTINEL_AUTOPLAY=1
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file" -ForegroundColor Green
}

# Start Docker Compose
Write-Host ""
Write-Host "Starting services with Docker Compose..." -ForegroundColor Cyan
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SENTINEL is starting!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📡 Services:" -ForegroundColor Cyan
    Write-Host "   Backend API:  http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:     http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Frontend UI:  http://localhost:5173" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 View logs:    docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "🛑 Stop:         docker-compose down" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Check health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    } catch {
        Write-Host "⏳ Backend is still starting... (check with: docker-compose logs -f backend)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Application started successfully!" -ForegroundColor Green
    Write-Host "Open your browser to http://localhost:5173" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Failed to start services. Check logs with: docker-compose logs" -ForegroundColor Red
    exit 1
}
