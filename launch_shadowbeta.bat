@echo off
setlocal enabledelayedexpansion

REM ShadowBeta Financial Dashboard Launcher
echo ========================================
echo 🚀 ShadowBeta Financial Dashboard Launcher
echo ========================================
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo Current working directory: %CD%
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ❌ Error: backend directory not found!
    echo Please make sure this script is in the PipEngine-main directory.
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ❌ Error: frontend directory not found!
    echo Please make sure this script is in the PipEngine-main directory.
    pause
    exit /b 1
)

echo ✅ Directory structure check passed
echo.

REM Check if .env file exists in backend
if not exist "backend\.env" (
    echo ❌ Error: backend/.env file not found!
    echo Please run setup_local.bat first to create the environment file.
    pause
    exit /b 1
)

echo ✅ Environment file found
echo.

REM Check if Python is installed
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
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
echo ✅ Node.js check passed
echo.

REM Check if Yarn is installed
echo 🔍 Checking Yarn installation...
yarn --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Yarn is not installed or not in PATH.
    echo Please install Yarn first: npm install -g yarn
    pause
    exit /b 1
)
echo ✅ Yarn check passed
echo.

echo ========================================
echo 🚀 Starting ShadowBeta Financial Dashboard...
echo ========================================
echo.

echo 📋 Starting services:
echo    • Backend API (Python/FastAPI) - Port 8000
echo    • Frontend Dashboard (React) - Port 3000
echo.

echo ⏳ Starting backend server...
start "ShadowBeta Backend" cmd /k "cd backend && echo Starting backend server... && python server.py"

echo ⏳ Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo ⏳ Starting frontend development server...
start "ShadowBeta Frontend" cmd /k "cd frontend && echo Starting frontend server... && yarn start"

echo.
echo ========================================
echo 🎉 ShadowBeta Financial Dashboard Launched!
echo ========================================
echo.
echo 🌐 Access your application at:
echo    • Frontend Dashboard: http://localhost:3000
echo    • Backend API: http://localhost:8000
echo.
echo 📊 API Documentation: http://localhost:8000/docs
echo.
echo ⚠️  Important Notes:
echo    • Keep both terminal windows open
echo    • Backend must be running for frontend to work
echo    • Press Ctrl+C in each terminal to stop the services
echo.
echo 🛑 To stop all services, close the terminal windows
echo.
echo Press any key to open the dashboard in your browser...
pause >nul

REM Open the frontend in default browser
start http://localhost:3000

echo.
echo 🌐 Opening ShadowBeta Dashboard in your browser...
echo.
echo 🎯 Your ShadowBeta Financial Dashboard is now running!
echo.
pause
