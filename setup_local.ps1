# Setup local development environment for ShadowBeta Financial Dashboard
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Setting up ShadowBeta Financial Dashboard..." -ForegroundColor Green
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
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: frontend directory not found!" -ForegroundColor Red
    Write-Host "Please make sure this script is in the PipEngine-main directory." -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Directory structure check passed" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $pythonVersion -ForegroundColor Green
        Write-Host "✅ Python check passed" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if Node.js is installed
Write-Host "🔍 Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $nodeVersion -ForegroundColor Green
        Write-Host "✅ Node.js check passed" -ForegroundColor Green
    } else {
        throw "Node.js not found"
    }
} catch {
    Write-Host "❌ Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if Yarn is installed
Write-Host "🔍 Checking Yarn installation..." -ForegroundColor Yellow
try {
    $yarnVersion = yarn --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $yarnVersion -ForegroundColor Green
        Write-Host "✅ Yarn check passed" -ForegroundColor Green
    } else {
        throw "Yarn not found"
    }
} catch {
    Write-Host "❌ Yarn is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Installing Yarn globally..." -ForegroundColor Yellow
    npm install -g yarn
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Yarn. Please install manually:" -ForegroundColor Red
        Write-Host "npm install -g yarn" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    $yarnVersion = yarn --version 2>&1
    Write-Host $yarnVersion -ForegroundColor Green
    Write-Host "✅ Yarn check passed" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📦 Installing Dependencies..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# Install backend dependencies
Write-Host ""
Write-Host "🔧 Installing backend dependencies..." -ForegroundColor Yellow
Set-Location "backend"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Backend dependencies installed successfully" -ForegroundColor Green

# Install frontend dependencies
Write-Host ""
Write-Host "🔧 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location "..\frontend"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
yarn install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Frontend dependencies installed successfully" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "⚙️ Creating Environment Files..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# Create .env file for backend
Write-Host ""
Write-Host "🔧 Creating backend environment file..." -ForegroundColor Yellow
Set-Location "..\backend"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
if (-not (Test-Path ".env")) {
    @"
# ShadowBeta Financial Dashboard Environment Configuration

# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=shadowbeta

# Required API Keys (Get these from the respective services)
FINNHUB_API_KEY=your_finnhub_key_here
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional Features
DISCORD_TOKEN=your_discord_token_here
CHANNEL_ID=your_channel_id_here
NEWS_API_KEY=your_news_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file in backend directory" -ForegroundColor Green
    Write-Host "⚠️  Please update the .env file with your actual API keys" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists in backend directory" -ForegroundColor Green
}

# Create .env file for frontend
Write-Host ""
Write-Host "🔧 Creating frontend environment file..." -ForegroundColor Yellow
Set-Location "..\frontend"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
if (-not (Test-Path ".env")) {
    @"
# ShadowBeta Frontend Environment Configuration
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file in frontend directory" -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists in frontend directory" -ForegroundColor Green
}

Set-Location ".."

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Update the backend/.env file with your API keys" -ForegroundColor White
Write-Host "2. Start MongoDB (if not already running)" -ForegroundColor White
Write-Host "3. Start the backend: cd backend && python server.py" -ForegroundColor White
Write-Host "4. Start the frontend: cd frontend && yarn start" -ForegroundColor White
Write-Host ""
Write-Host "🌐 The application will be available at:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "📚 For more information, see the README.md file" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
