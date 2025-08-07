# ShadowBeta Ultimate Launcher (PowerShell)
# This script provides comprehensive setup and launch functionality

param(
    [switch]$Quick,
    [switch]$Setup
)

# Set console colors and encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "ShadowBeta Ultimate Launcher"

# Color functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Step { param($Message) Write-Host "🔧 $Message" -ForegroundColor Blue }

# Header
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "    🚀 ShadowBeta Ultimate Launcher" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Write-Success "Working directory: $(Get-Location)"

# Check directory structure
if (-not (Test-Path "backend\server.py")) {
    Write-Error "backend\server.py not found!"
    Write-Info "Make sure you're running this from the PipEngine-main directory"
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend\package.json")) {
    Write-Error "frontend\package.json not found!"
    Write-Info "Make sure you're running this from the PipEngine-main directory"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Success "Directory structure verified"

# Check and create .env files
Write-Host ""
Write-Step "Checking environment files..."

if (-not (Test-Path "frontend\.env")) {
    Write-Warning "Creating frontend .env file..."
    "REACT_APP_BACKEND_URL=http://localhost:8000" | Out-File -FilePath "frontend\.env" -Encoding UTF8
    Write-Success "Frontend .env created"
}
else {
    Write-Success "Frontend .env exists"
}

if (-not (Test-Path "backend\.env")) {
    Write-Warning "Creating backend .env file with default settings..."
    @"
# ShadowBeta Financial Dashboard Environment Configuration

# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=shadowbeta

# Required API Keys
FINNHUB_API_KEY=d2431dpr01qmb590bi10d2431dpr01qmb590bi1g
GEMINI_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional Features
DISCORD_TOKEN=MTM5OTEzODk5ODMzNjc1Mzc3NQ.GxegZp.gO3gEZ0j8-8IXmrMtph6Qdbqtx7SKGNcEt0Jjs
CHANNEL_ID=1398832733102542890
NEWS_API_KEY=a95cbb6269564b19a4a3fbb239d0bb86

# Additional API Keys
VITE_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
POLYGON_API_KEY=nIvxYsjmVczvlHip5okWPz51iAJqCFrx

# Server Configuration
HOST=0.0.0.0
PORT=8000
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
    Write-Success "Backend .env created"
}
else {
    Write-Success "Backend .env exists"
}

# Check prerequisites
Write-Host ""
Write-Step "Checking prerequisites..."

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
}
catch {
    Write-Error "Python not found! Please install Python 3.8+"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js found: $nodeVersion"
}
catch {
    Write-Error "Node.js not found! Please install Node.js 16+"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Yarn
try {
    $yarnVersion = yarn --version 2>&1
    Write-Success "Yarn found: $yarnVersion"
}
catch {
    Write-Warning "Yarn not found, installing..."
    try {
        npm install -g yarn
        Write-Success "Yarn installed"
    }
    catch {
        Write-Error "Failed to install Yarn"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install dependencies if needed
Write-Host ""
Write-Step "Checking dependencies..."

# Backend dependencies
if (-not (Test-Path "backend\venv")) {
    Write-Warning "Creating Python virtual environment..."
    Set-Location backend
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
    pip install -r requirements.txt
    Set-Location ..
    Write-Success "Backend dependencies installed"
}
else {
    Write-Success "Backend virtual environment exists"
}

# Frontend dependencies
if (-not (Test-Path "frontend\node_modules")) {
    Write-Warning "Installing frontend dependencies..."
    Set-Location frontend
    yarn install
    Set-Location ..
    Write-Success "Frontend dependencies installed"
}
else {
    Write-Success "Frontend dependencies exist"
}

# Kill existing processes
Write-Host ""
Write-Step "Checking for existing processes..."

$processes8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
$processes3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess

foreach ($processId in $processes8000) {
    Write-Warning "Killing process on port 8000: $processId"
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

foreach ($processId in $processes3000) {
    Write-Warning "Killing process on port 3000: $processId"
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

# Start backend
Write-Host ""
Write-Step "Starting ShadowBeta Backend..."
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir
    Set-Location backend
    & ".\venv\Scripts\Activate.ps1"
    python server.py
}

# Wait for backend to start
Write-Info "Waiting for backend to start..."
Start-Sleep -Seconds 8

# Test backend connection
Write-Step "Testing backend connection..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction Stop
    Write-Success "Backend is running on http://localhost:8000"
}
catch {
    Write-Warning "Backend not responding yet, waiting a bit more..."
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction Stop
        Write-Success "Backend is running on http://localhost:8000"
    }
    catch {
        Write-Error "Backend failed to start properly"
        Write-Info "Check the backend window for error messages"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Start frontend
Write-Host ""
Write-Step "Starting ShadowBeta Frontend..."
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir
    Set-Location frontend
    yarn start
}

# Wait for frontend to start
Write-Info "Waiting for frontend to start..."
Start-Sleep -Seconds 10

# Test frontend connection
Write-Step "Testing frontend connection..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/" -TimeoutSec 5 -ErrorAction Stop
    Write-Success "Frontend is running on http://localhost:3000"
    $frontendUrl = "http://localhost:3000"
}
catch {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3001/" -TimeoutSec 5 -ErrorAction Stop
        Write-Success "Frontend is running on http://localhost:3001"
        $frontendUrl = "http://localhost:3001"
    }
    catch {
        Write-Warning "Frontend not responding yet, but it may still be starting..."
        $frontendUrl = "http://localhost:3000"
    }
}

# Open browser
Write-Host ""
Write-Step "Opening browser..."
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"
Start-Sleep -Seconds 2
Start-Process "http://localhost:3001"

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "    🎉 ShadowBeta is Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Dashboard: $frontendUrl" -ForegroundColor White
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Both backend and frontend are running in separate windows" -ForegroundColor Gray
Write-Host "   - Close those windows to stop the services" -ForegroundColor Gray
Write-Host "   - The dashboard should load with real-time stock data" -ForegroundColor Gray
Write-Host "   - If you see a white screen, wait a few more seconds for data to load" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit this launcher"
