@echo off
REM Windows batch file to run the Flask server for the Phishing Detection Extension
REM This file should be double-clicked to start the server

setlocal enabledelayedexpansion

title Phishing Detection Extension - Flask Server

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🔒  Phishing Detection Extension - Flask Server          ║
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

REM Check if flask is installed
echo Checking for required packages...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Flask is not installed
    echo Installing Flask and Flask-CORS...
    echo.
    pip install flask flask-cors
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install Flask packages
        pause
        exit /b 1
    )
)

echo ✅ Flask is installed
echo.

REM Run the Flask server
echo Starting Flask server...
echo.
echo ═════════════════════════════════════════════════════════════
echo Server will run on: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ═════════════════════════════════════════════════════════════
echo.

python flask_server.py

if errorlevel 1 (
    echo.
    echo ERROR: Flask server failed to start
    pause
    exit /b 1
)

pause
