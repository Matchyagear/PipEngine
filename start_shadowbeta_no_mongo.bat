@echo off
title ShadowBeta Financial Dashboard (No MongoDB)

echo.
echo ========================================
echo    🚀 ShadowBeta Financial Dashboard
echo ========================================
echo.
echo Starting your financial dashboard...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Set environment variable to disable MongoDB
set MONGODB_DISABLED=true

REM Start backend in new window
echo Starting backend server (Port 8000, MongoDB disabled)...
start "ShadowBeta Backend" cmd /k "cd backend && set MONGODB_DISABLED=true && python server.py"

REM Wait for backend to initialize
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server (Port 3000)...
start "ShadowBeta Frontend" cmd /k "cd frontend && yarn start"

REM Wait for frontend to initialize
echo Waiting for frontend to start...
timeout /t 8 /nobreak >nul

REM Open browser
echo Opening dashboard in browser...
start http://localhost:3000

echo.
echo ========================================
echo    🎉 ShadowBeta is now running!
echo ========================================
echo.
echo 🌐 Dashboard: http://localhost:3000
echo 📊 API Docs: http://localhost:8000/docs
echo 🔧 Backend API: http://localhost:8000
echo.
echo Keep the terminal windows open to run the services.
echo Close the windows to stop the services.
echo.
echo If you see a white screen, wait a few more seconds
echo for the data to load from the backend.
echo.
pause
