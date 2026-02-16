@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting TestStrategy Agent...

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+
    exit /b 1
)

REM Install backend dependencies
echo 📦 Installing backend dependencies...
cd teststrategy-agent\backend
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ Failed to install backend dependencies
    exit /b 1
)

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd ..\frontend
call npm install --silent
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    exit /b 1
)

REM Build frontend
echo 🔨 Building frontend...
call npm run build
if errorlevel 1 (
    echo ❌ Failed to build frontend
    exit /b 1
)

REM Copy build to backend
if exist ..\backend\static rmdir /s /q ..\backend\static
xcopy /s /e /i /q dist ..\backend\static

REM Start server
cd ..\backend
echo.
echo ✅ TestStrategy Agent is ready!
echo 🌐 Open http://localhost:8000 in your browser
echo.
uvicorn main:app --host 0.0.0.0 --port 8000
