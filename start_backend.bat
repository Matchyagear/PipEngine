@echo off
echo Starting ShadowBeta Backend...
cd /d "%~dp0backend"
python server.py > server_output.log 2>&1
if %ERRORLEVEL% neq 0 (
    echo Failed to start backend server. Check server_output.log for details.
    type server_output.log
    pause
) else (
    echo Backend server started successfully on port 8001
    pause
)
