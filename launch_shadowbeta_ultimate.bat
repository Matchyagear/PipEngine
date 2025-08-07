@echo off
setlocal enabledelayedexpansion
title ShadowBeta Ultimate Launcher

echo.
echo ========================================
echo    🚀 ShadowBeta Ultimate Launcher
echo ========================================
echo.

:: Change to the correct directory
cd /d "%~dp0"
echo ✅ Working directory: %CD%

:: Check if we're in the right place
if not exist "backend\server.py" (
    echo ❌ Error: backend\server.py not found!
    echo 💡 Make sure you're running this from the PipEngine-main directory
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ❌ Error: frontend\package.json not found!
    echo 💡 Make sure you're running this from the PipEngine-main directory
    pause
    exit /b 1
)

echo ✅ Directory structure verified

:: Check if .env files exist and create if needed
echo.
echo 📁 Checking environment files...

if not exist "frontend\.env" (
    echo ⚠️  Creating frontend .env file...
    echo REACT_APP_BACKEND_URL=http://localhost:8000 > frontend\.env
    echo ✅ Frontend .env created
) else (
    echo ✅ Frontend .env exists
)

if not exist "backend\.env" (
    echo ⚠️  Creating backend .env file with default settings...
    (
        echo # ShadowBeta Financial Dashboard Environment Configuration
        echo.
        echo # Database Configuration
        echo MONGO_URL=mongodb://localhost:27017
        echo DB_NAME=shadowbeta
        echo.
        echo # Required API Keys
        echo FINNHUB_API_KEY=d2431dpr01qmb590bi10d2431dpr01qmb590bi1g
        echo GEMINI_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
        echo OPENAI_API_KEY=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
        echo ANTHROPIC_API_KEY=your_anthropic_key_here
        echo.
        echo # Optional Features
        echo DISCORD_TOKEN=MTM5OTEzODk5ODMzNjc1Mzc3NQ.GxegZp.gO3gEZ0j8-8IXmrMtph6Qdbqtx7SKGNcEt0Jjs
        echo CHANNEL_ID=1398832733102542890
        echo NEWS_API_KEY=your_news_api_key_here
        echo.
        echo # Additional API Keys
        echo VITE_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
        echo POLYGON_API_KEY=nIvxYsjmVczvlHip5okWPz51iAJqCFrx
        echo.
        echo # Server Configuration
        echo HOST=0.0.0.0
        echo PORT=8000
    ) > backend\.env
    echo ✅ Backend .env created
) else (
    echo ✅ Backend .env exists
)

:: Check if Python is available
echo.
echo 🐍 Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python found

:: Check if Node.js is available
echo.
echo 📦 Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js 16+
    pause
    exit /b 1
)
echo ✅ Node.js found

:: Check if Yarn is available
echo.
echo 🧶 Checking Yarn...
yarn --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Yarn not found, installing...
    npm install -g yarn
    if errorlevel 1 (
        echo ❌ Failed to install Yarn
        pause
        exit /b 1
    )
    echo ✅ Yarn installed
) else (
    echo ✅ Yarn found
)

:: Install backend dependencies if needed
echo.
echo 📦 Checking backend dependencies...
if not exist "backend\venv" (
    echo ⚠️  Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
    echo ✅ Backend dependencies installed
) else (
    echo ✅ Backend virtual environment exists
)

:: Install frontend dependencies if needed
echo.
echo 📦 Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo ⚠️  Installing frontend dependencies...
    cd frontend
    yarn install
    cd ..
    echo ✅ Frontend dependencies installed
) else (
    echo ✅ Frontend dependencies exist
)

:: Kill any existing processes on ports 8000 and 3000
echo.
echo 🔄 Checking for existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo ⚠️  Killing process on port 8000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo ⚠️  Killing process on port 3000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: Wait a moment for processes to close
timeout /t 2 /nobreak >nul

:: Start backend in a new window
echo.
echo 🚀 Starting ShadowBeta Backend...
start "ShadowBeta Backend" cmd /k "cd /d "%~dp0" && cd backend && call venv\Scripts\activate.bat && python server.py"

:: Wait for backend to start
echo ⏳ Waiting for backend to start...
timeout /t 8 /nobreak >nul

:: Test backend connection
echo 🔍 Testing backend connection...
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend not responding yet, waiting a bit more...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:8000/ >nul 2>&1
    if errorlevel 1 (
        echo ❌ Backend failed to start properly
        echo 💡 Check the backend window for error messages
        pause
        exit /b 1
    )
)
echo ✅ Backend is running on http://localhost:8000

:: Start frontend in a new window
echo.
echo 🚀 Starting ShadowBeta Frontend...
start "ShadowBeta Frontend" cmd /k "cd /d "%~dp0" && cd frontend && yarn start"

:: Wait for frontend to start
echo ⏳ Waiting for frontend to start...
timeout /t 10 /nobreak >nul

:: Test frontend connection
echo 🔍 Testing frontend connection...
curl -s http://localhost:3000/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend not responding on port 3000, checking port 3001...
    curl -s http://localhost:3001/ >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  Frontend not responding yet, but it may still be starting...
    ) else (
        echo ✅ Frontend is running on http://localhost:3001
    )
) else (
    echo ✅ Frontend is running on http://localhost:3000
)

:: Open browser
echo.
echo 🌐 Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000
timeout /t 2 /nobreak >nul
start http://localhost:3001

echo.
echo ========================================
echo    🎉 ShadowBeta is Ready!
echo ========================================
echo.
echo 📊 Dashboard: http://localhost:3000 (or 3001)
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo 💡 Tips:
echo    - Both backend and frontend are running in separate windows
echo    - Close those windows to stop the services
echo    - The dashboard should load with real-time stock data
echo    - If you see a white screen, wait a few more seconds for data to load
echo.
echo Press any key to exit this launcher...
pause >nul
