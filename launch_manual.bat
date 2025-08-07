@echo off
title ShadowBeta Manual Launcher

echo.
echo ========================================
echo    🚀 ShadowBeta Manual Launcher
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

echo.
echo ========================================
echo    Manual Launch Options
echo ========================================
echo.
echo 1. Start Backend Only
echo 2. Start Frontend Only
echo 3. Start Both Services
echo 4. Open Browser
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto open_browser
if "%choice%"=="5" goto exit
goto invalid

:start_backend
echo.
echo Starting Backend...
start "ShadowBeta Backend" cmd /k "cd /d "%~dp0" && cd backend && python server.py"
echo Backend started in new window
pause
goto menu

:start_frontend
echo.
echo Starting Frontend...
start "ShadowBeta Frontend" cmd /k "cd /d "%~dp0" && cd frontend && yarn start"
echo Frontend started in new window
pause
goto menu

:start_both
echo.
echo Starting both services...
echo Starting Backend...
start "ShadowBeta Backend" cmd /k "cd /d "%~dp0" && cd backend && python server.py"
timeout /t 5 /nobreak >nul
echo Starting Frontend...
start "ShadowBeta Frontend" cmd /k "cd /d "%~dp0" && cd frontend && yarn start"
echo Both services started in separate windows
pause
goto menu

:open_browser
echo.
echo Opening browser...
start http://localhost:3000
timeout /t 2 /nobreak >nul
start http://localhost:3001
echo Browser opened
pause
goto menu

:invalid
echo Invalid choice. Please try again.
pause
goto menu

:menu
cls
echo.
echo ========================================
echo    Manual Launch Options
echo ========================================
echo.
echo 1. Start Backend Only
echo 2. Start Frontend Only
echo 3. Start Both Services
echo 4. Open Browser
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto open_browser
if "%choice%"=="5" goto exit
goto invalid

:exit
echo Goodbye!
exit /b 0
