@echo off
REM FinSolve RBAC Assistant - Windows Start Script
REM Author: Dr. Erick K. Yegon

echo.
echo ========================================
echo  FinSolve RBAC Assistant
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "fin_env\Scripts\activate.bat" (
    echo ERROR: Virtual environment 'fin_env' not found!
    echo Please create it first with: python -m venv fin_env
    echo Then install requirements: fin_env\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call fin_env\Scripts\activate.bat

REM Check if requirements are installed
python -c "import fastapi, streamlit, langchain" 2>nul
if errorlevel 1 (
    echo ERROR: Required packages not installed!
    echo Please install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Starting FinSolve RBAC Assistant...
echo.
echo IMPORTANT: This is the ONLY supported way to run the application.
echo Do NOT use: python -m src.api.main or python src/api/main.py
echo.

REM Run the application
python main.py

echo.
echo Application stopped.
pause
