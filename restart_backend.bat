@echo off
title Restart Backend with New NewsAPI Key

echo.
echo ========================================
echo    🔄 Restarting Backend with NewsAPI
echo ========================================
echo.

:: Change to the correct directory
cd /d "%~dp0"
echo Working directory: %CD%

:: Kill existing backend processes
echo Killing existing backend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Killing process on port 8000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: Wait a moment
timeout /t 3 /nobreak >nul

:: Update backend .env with NewsAPI key
echo Updating backend .env with NewsAPI key...
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

echo Backend .env updated with NewsAPI key

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
    echo WARNING: Backend not responding yet, but it should start soon...
) else (
    echo Backend is running on http://localhost:8000
)

echo.
echo ========================================
echo    Backend Restarted!
echo ========================================
echo.
echo The backend has been restarted with the new NewsAPI key.
echo NewsAPI errors should now be resolved.
echo.
echo Keep the backend window open!
echo.
pause
