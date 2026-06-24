@echo off
REM ============================================================
REM  VA Creator Launcher — Windows (.bat)
REM  Starts the Streamlit dashboard for VA Creator
REM ============================================================

title VA Creator — AI-Powered Tutorial Video Generator

echo.
echo  ========================================
echo   VA Creator v1.3.0 — Launcher (Windows)
echo  ========================================
echo.

REM Navigate to the script's own directory
cd /d "%~dp0"

REM --- Check Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM --- Check / Create Virtual Environment ---
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

REM --- Activate Virtual Environment ---
call venv\Scripts\activate.bat

REM --- Install Python Dependencies ---
if exist "requirements.txt" (
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt --quiet
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Some Python dependencies may have failed to install.
    ) else (
        echo [OK] Python dependencies installed.
    )
)

REM --- Install Node.js Dependencies (if package.json exists) ---
if exist "package.json" (
    where npm >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        if not exist "node_modules" (
            echo [INFO] Installing Node.js dependencies...
            npm install --quiet
            if %ERRORLEVEL% neq 0 (
                echo [WARNING] Some Node.js dependencies may have failed to install.
            ) else (
                echo [OK] Node.js dependencies installed.
            )
        )
    ) else (
        echo [WARNING] npm not found. MCP server integrations may not work.
        echo          Install Node.js from https://nodejs.org/ for full functionality.
    )
)

REM --- Check .env File ---
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo          Copy env.example to .env and add your API keys:
    echo            copy env.example .env
    echo.
)

REM --- Launch Streamlit ---
echo.
echo [INFO] Starting VA Creator Dashboard...
echo        Open http://localhost:8501 in your browser.
echo        Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
