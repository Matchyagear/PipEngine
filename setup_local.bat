@echo off
setlocal enabledelayedexpansion

REM Setup local development environment for ShadowBeta Financial Dashboard
echo ========================================
echo 🚀 Setting up ShadowBeta Financial Dashboard...
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ❌ Error: backend directory not found!
    echo Please run this script from the PipEngine-main directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ❌ Error: frontend directory not found!
    echo Please run this script from the PipEngine-main directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo ✅ Directory structure check passed
echo.

REM Check if Python is installed
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo ✅ Python check passed
echo.

REM Check if Node.js is installed
echo 🔍 Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
node --version
echo ✅ Node.js check passed
echo.

REM Check if Yarn is installed
echo 🔍 Checking Yarn installation...
yarn --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Yarn is not installed or not in PATH.
    echo Installing Yarn globally...

    npm install -g yarn
    if errorlevel 1 (
        echo ❌ Failed to install Yarn. Please install manually:
        echo npm install -g yarn
        pause
        exit /b 1
    )
)
yarn --version
echo ✅ Yarn check passed
echo.

echo ========================================
echo 📦 Installing Dependencies...
echo ========================================

REM Install backend dependencies
echo.
echo 🔧 Installing backend dependencies...
cd backend
echo Current directory: %CD%
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install backend dependencies
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed successfully

REM Install frontend dependencies
echo.
echo 🔧 Installing frontend dependencies...
cd ..\frontend
echo Current directory: %CD%
yarn install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed successfully

echo ========================================
echo ⚙️ Creating Environment Files...
echo ========================================

REM Create .env file for backend
echo.
echo 🔧 Creating backend environment file...
cd ..\backend
echo Current directory: %CD%
if not exist .env (
    (
        echo # ShadowBeta Financial Dashboard Environment Configuration
        echo.
        echo # Database Configuration
        echo MONGO_URL=mongodb://localhost:27017
        echo DB_NAME=shadowbeta
        echo.
        echo # Required API Keys ^(Get these from the respective services^)
        echo FINNHUB_API_KEY=your_finnhub_key_here
        echo GEMINI_API_KEY=your_gemini_key_here
        echo OPENAI_API_KEY=your_openai_key_here
        echo ANTHROPIC_API_KEY=your_anthropic_key_here
        echo.
        echo # Optional Features
        echo DISCORD_TOKEN=your_discord_token_here
        echo CHANNEL_ID=your_channel_id_here
        echo NEWS_API_KEY=your_news_api_key_here
        echo.
        echo # Server Configuration
        echo HOST=0.0.0.0
        echo PORT=8000
    ) > .env
    echo ✅ Created .env file in backend directory
    echo ⚠️  Please update the .env file with your actual API keys
) else (
    echo ✅ .env file already exists in backend directory
)

REM Create .env file for frontend
echo.
echo 🔧 Creating frontend environment file...
cd ..\frontend
echo Current directory: %CD%
if not exist .env (
    (
        echo # ShadowBeta Frontend Environment Configuration
        echo REACT_APP_BACKEND_URL=http://localhost:8000
        echo WDS_SOCKET_PORT=443
    ) > .env
    echo ✅ Created .env file in frontend directory
) else (
    echo ✅ .env file already exists in frontend directory
)

cd ..

echo ========================================
echo 🎉 Setup Complete!
echo ========================================
echo.
echo 📋 Next steps:
echo 1. Update the backend/.env file with your API keys
echo 2. Start MongoDB ^(if not already running^)
echo 3. Start the backend: cd backend ^&^& python server.py
echo 4. Start the frontend: cd frontend ^&^& yarn start
echo.
echo 🌐 The application will be available at:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo.
echo 📚 For more information, see the README.md file
echo.
echo Press any key to exit...
pause >nul
