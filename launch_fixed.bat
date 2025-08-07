@echo off
title ShadowBeta Fixed Launcher

echo.
echo ========================================
echo    🚀 ShadowBeta Fixed Launcher
echo ========================================
echo.

:: Change to the correct directory
cd /d "%~dp0"
echo Working directory: %CD%

:: Check if we're in the right place
if not exist "backend\server.py" (
    echo ERROR: backend\server.py not found!
    echo Make sure you're running this from the PipEngine-main directory
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ERROR: frontend\package.json not found!
    echo Make sure you're running this from the PipEngine-main directory
    pause
    exit /b 1
)

echo Directory structure verified

:: Create .env files if they don't exist
if not exist "frontend\.env" (
    echo Creating frontend .env file...
    echo REACT_APP_BACKEND_URL=http://localhost:8000 > frontend\.env
    echo Frontend .env created
)

if not exist "backend\.env" (
    echo Creating backend .env file...
    (
        echo FINNHUB_API_KEY=d2431dpr01qmb590bi10d2431dpr01qmb590bi1g
        echo GEMINI_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
        echo OPENAI_API_KEY=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
        echo DISCORD_TOKEN=MTM5OTEzODk5ODMzNjc1Mzc3NQ.GxegZp.gO3gEZ0j8-8IXmrMtph6Qdbqtx7SKGNcEt0Jjs
        echo CHANNEL_ID=1398832733102542890
        echo NEWS_API_KEY=a95cbb6269564b19a4a3fbb239d0bb86
        echo VITE_API_KEY=AIzaSyBAEvD2LaQKLMkp-Bc5XQilwKL2y4f9VlA
        echo POLYGON_API_KEY=nIvxYsjmVczvlHip5okWPz51iAJqCFrx
        echo PORT=8000
    ) > backend\.env
    echo Backend .env created
)

:: Kill any existing processes on ports 8000 and 3000
echo.
echo Checking for existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Killing process on port 8000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo Killing process on port 3000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: Wait a moment
timeout /t 3 /nobreak >nul

:: Start backend
echo.
echo Starting ShadowBeta Backend...
start "ShadowBeta Backend" cmd /k "cd /d "%~dp0" && cd backend && python server.py"

:: Wait for backend to start
echo Waiting for backend to start...
timeout /t 10 /nobreak >nul

:: Test backend
echo Testing backend connection...
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend not responding yet, but continuing...
) else (
    echo Backend is running on http://localhost:8000
)

:: Start frontend with specific port
echo.
echo Starting ShadowBeta Frontend on port 3001...
start "ShadowBeta Frontend" cmd /k "cd /d "%~dp0" && cd frontend && set PORT=3001 && yarn start"

:: Wait for frontend to start
echo Waiting for frontend to start...
timeout /t 15 /nobreak >nul

:: Open browser
echo.
echo Opening browser...
start http://localhost:3001
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo    ShadowBeta is Starting!
echo ========================================
echo.
echo IMPORTANT:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3001 (or 3000)
echo.
echo If you see a white screen:
echo 1. Wait 30-60 seconds for data to load
echo 2. Check both console windows for errors
echo 3. Try refreshing the browser
echo.
echo Keep both backend and frontend windows open!
echo.
pause
