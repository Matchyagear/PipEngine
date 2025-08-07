@echo off
echo ========================================
echo 🔍 Debug Setup Script
echo ========================================
echo.
echo This script will test basic functionality to help identify issues.
echo.

echo Current directory: %CD%
echo.

echo Testing basic commands:
echo.

echo 1. Testing echo command:
echo Hello World
echo.

echo 2. Testing directory listing:
dir
echo.

echo 3. Testing if backend directory exists:
if exist "backend" (
    echo ✅ Backend directory found
) else (
    echo ❌ Backend directory not found
)
echo.

echo 4. Testing if frontend directory exists:
if exist "frontend" (
    echo ✅ Frontend directory found
) else (
    echo ❌ Frontend directory not found
)
echo.

echo 5. Testing Python:
python --version
if errorlevel 1 (
    echo ❌ Python not found or not in PATH
) else (
    echo ✅ Python found
)
echo.

echo 6. Testing Node.js:
node --version
if errorlevel 1 (
    echo ❌ Node.js not found or not in PATH
) else (
    echo ✅ Node.js found
)
echo.

echo 7. Testing Yarn:
yarn --version
if errorlevel 1 (
    echo ❌ Yarn not found or not in PATH
) else (
    echo ✅ Yarn found
)
echo.

echo ========================================
echo Debug test complete!
echo ========================================
echo.
echo If you see any ❌ errors above, those might be causing issues.
echo.
echo Press any key to exit...
pause >nul
