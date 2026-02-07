@echo off
REM Windows batch file to test the Flask server for the Phishing Detection Extension
REM Run this AFTER starting the Flask server

setlocal enabledelayedexpansion

title Phishing Detection Extension - Backend Tests

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🔒  Phishing Detection Extension - Backend Tests         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if requests is installed
pip show requests >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ requests library is not installed
    echo Installing requests...
    echo.
    pip install requests
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install requests
        pause
        exit /b 1
    )
)

echo ✅ requests library is installed
echo.

REM Run the test script
echo Running backend tests...
echo.
echo Make sure the Flask server is running!
echo If it's not, open another terminal and run: python flask_server.py
echo.

python test_extension_backend.py

pause
