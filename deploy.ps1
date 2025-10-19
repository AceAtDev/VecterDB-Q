# VectorDB-Q Docker Deployment (Windows)

Write-Host "`n🚀 VectorDB-Q Docker Deployment" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running!" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  No .env file found. Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Created .env file`n" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Edit .env and add your Cohere API key!" -ForegroundColor Yellow
    Write-Host "   COHERE_API_KEY=your_actual_key_here`n" -ForegroundColor White
    Read-Host "Press Enter after updating .env file"
}

# Check if Cohere API key is set
$envContent = Get-Content .env -Raw
if ($envContent -match "your_cohere_api_key_here") {
    Write-Host "⚠️  WARNING: You haven't set your Cohere API key in .env" -ForegroundColor Yellow
    Write-Host "   The application won't work without it!`n" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

Write-Host "`n📦 Building Docker image..." -ForegroundColor Cyan
docker-compose build

Write-Host "`n🚀 Starting services..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "`n⏳ Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Service is healthy!`n" -ForegroundColor Green
        Write-Host "🎉 Deployment successful!`n" -ForegroundColor Green
        Write-Host "📍 Access your application:" -ForegroundColor Cyan
        Write-Host "   Frontend:    http://localhost:8000/" -ForegroundColor White
        Write-Host "   API Docs:    http://localhost:8000/docs" -ForegroundColor White
        Write-Host "   Health:      http://localhost:8000/health`n" -ForegroundColor White
        Write-Host "📋 Useful commands:" -ForegroundColor Cyan
        Write-Host "   docker-compose logs -f       # View logs" -ForegroundColor White
        Write-Host "   docker-compose restart       # Restart services" -ForegroundColor White
        Write-Host "   docker-compose down          # Stop services`n" -ForegroundColor White
    }
} catch {
    Write-Host "⚠️  Service is not responding yet" -ForegroundColor Yellow
    Write-Host "   Check logs: docker-compose logs -f`n" -ForegroundColor White
}
