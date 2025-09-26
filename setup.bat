@echo off
echo ================================================
echo    Student Attendance System - Setup Script
echo ================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found! Creating virtual environment...
python -m venv attendance_env

echo Activating virtual environment...
call attendance_env\Scripts\activate.bat

echo Installing required packages...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ================================================
echo    Setup completed successfully!
echo ================================================
echo.
echo To run the application:
echo 1. Run: start_server.bat
echo 2. Open browser: http://localhost:5000
echo.
echo Press any key to continue...
pause >nul