@echo off
REM Overton Analyzer - Run Script for Windows

echo Starting Overton Policy Citation Analyzer...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.7+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Check for .env file
if not exist ".env" (
    echo No .env file found. Copy .env.example to .env and add your API key.
    echo You can also enter the API key in the web interface.
)

echo.
echo Setup complete!
echo.
echo Starting application...
echo Access the web interface at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python app.py
