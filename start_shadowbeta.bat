@echo off
title ShadowBeta Quick Start

echo.
echo 🚀 Starting ShadowBeta...
echo.

:: Change to correct directory
cd /d "%~dp0"

:: Kill existing processes
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

:: Start backend
start "Backend" cmd /k "cd /d "%~dp0" && cd backend && python server.py"

:: Wait and start frontend
timeout /t 5 /nobreak >nul
start "Frontend" cmd /k "cd /d "%~dp0" && cd frontend && yarn start"

:: Wait and open browser
timeout /t 8 /nobreak >nul
start http://localhost:3000
start http://localhost:3001

echo ✅ ShadowBeta started!
echo 📊 Dashboard: http://localhost:3000 (or 3001)
echo 🔧 API: http://localhost:8000
