@echo off
echo ========================================================
echo   Starting FrameFlow AI - Intelligent B-roll Studio
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Checking Python environment...
set PYTHON_EXE=C:\Users\Lenovo\Python311\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [2/2] Launching Unified Server (Backend API + Frontend Studio)...
echo.
echo ========================================================
echo   Studio URL:   http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo ========================================================
echo Press Ctrl+C to stop the server.
echo.

"%PYTHON_EXE%" backend/app/main.py
pause
