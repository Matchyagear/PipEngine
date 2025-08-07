@echo off
title ShadowBeta Financial Dashboard (No CRACO)

echo.
echo ========================================
echo    🚀 ShadowBeta Financial Dashboard
echo ========================================
echo.
echo Starting your financial dashboard...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Start backend in new window
echo Starting backend server...
start "ShadowBeta Backend" cmd /k "cd backend && python server.py"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start frontend in new window using react-scripts directly
echo Starting frontend server (using react-scripts)...
start "ShadowBeta Frontend" cmd /k "cd frontend && npx react-scripts start"

REM Wait a moment
timeout /t 3 /nobreak >nul

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
echo.
echo Keep the terminal windows open to run the services.
echo Close the windows to stop the services.
echo.
pause
