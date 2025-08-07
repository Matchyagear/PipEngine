@echo off
title ShadowBeta Clean Start

echo.
echo 🚀 Starting ShadowBeta (Clean Version)...
echo.

:: Change to correct directory
cd /d "%~dp0"

:: Kill existing processes
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001') do taskkill /f /pid %%a >nul 2>&1

:: Start backend
start "Backend" cmd /k "cd /d "%~dp0" && cd backend && python server.py"

:: Wait and start frontend on port 3001 only
timeout /t 5 /nobreak >nul
start "Frontend" cmd /k "cd /d "%~dp0" && cd frontend && set PORT=3001 && yarn start"

:: Wait and open browser to port 3001 only
timeout /t 8 /nobreak >nul
start http://localhost:3001

echo ✅ ShadowBeta started!
echo 📊 Dashboard: http://localhost:3001
echo 🔧 API: http://localhost:8000
