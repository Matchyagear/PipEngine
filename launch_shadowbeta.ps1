# ShadowBeta Financial Dashboard Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 ShadowBeta Financial Dashboard Launcher" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to the directory where this script is located
Set-Location $PSScriptRoot

Write-Host "Current working directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend")) {
    Write-Host "❌ Error: backend directory not found!" -ForegroundColor Red
    Write-Host "Please make sure this script is in the PipEngine-main directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: frontend directory not found!" -ForegroundColor Red
    Write-Host "Please make sure this script is in the PipEngine-main directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Directory structure check passed" -ForegroundColor Green
Write-Host ""

# Check if .env file exists in backend
if (-not (Test-Path "backend\.env")) {
    Write-Host "❌ Error: backend/.env file not found!" -ForegroundColor Red
    Write-Host "Please run setup_local.bat first to create the environment file." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Environment file found" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python check passed" -ForegroundColor Green
    }
    else {
        throw "Python not found"
    }
}
catch {
    Write-Host "❌ Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if Node.js is installed
Write-Host "🔍 Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Node.js check passed" -ForegroundColor Green
    }
    else {
        throw "Node.js not found"
    }
}
catch {
    Write-Host "❌ Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if Yarn is installed
Write-Host "🔍 Checking Yarn installation..." -ForegroundColor Yellow
try {
    $yarnVersion = yarn --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Yarn check passed" -ForegroundColor Green
    }
    else {
        throw "Yarn not found"
    }
}
catch {
    Write-Host "❌ Yarn is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Yarn first: npm install -g yarn" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Starting ShadowBeta Financial Dashboard..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Starting services:" -ForegroundColor Yellow
Write-Host "   • Backend API (Python/FastAPI) - Port 8000" -ForegroundColor White
Write-Host "   • Frontend Dashboard (React) - Port 3000" -ForegroundColor White
Write-Host ""

# Start backend server
Write-Host "⏳ Starting backend server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    Set-Location "backend"
    python server.py
}

# Wait a moment for backend to initialize
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start frontend server
Write-Host "⏳ Starting frontend development server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    Set-Location "frontend"
    yarn start
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 ShadowBeta Financial Dashboard Launched!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access your application at:" -ForegroundColor Yellow
Write-Host "   • Frontend Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "📊 API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Important Notes:" -ForegroundColor Yellow
Write-Host "   • Services are running in background jobs" -ForegroundColor White
Write-Host "   • Backend must be running for frontend to work" -ForegroundColor White
Write-Host "   • Use Stop-Job to stop services" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop all services, press Ctrl+C" -ForegroundColor Red
Write-Host ""

# Ask user if they want to open the dashboard
$openBrowser = Read-Host "Open the dashboard in your browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Write-Host "🌐 Opening ShadowBeta Dashboard in your browser..." -ForegroundColor Green
    Start-Process "http://localhost:3000"
}

Write-Host ""
Write-Host "🎯 Your ShadowBeta Financial Dashboard is now running!" -ForegroundColor Green
Write-Host ""

# Keep the script running and show job status
try {
    while ($true) {
        $backendStatus = Get-Job -Id $backendJob.Id | Select-Object -ExpandProperty State
        $frontendStatus = Get-Job -Id $frontendJob.Id | Select-Object -ExpandProperty State

        Write-Host "Status: Backend [$backendStatus] | Frontend [$frontendStatus]" -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
}
catch {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
}
