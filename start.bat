@echo off
REM Quick start script for GPT-RAG Ingestion on Windows

echo ========================================
echo GPT-RAG Ingestion - Quick Start
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create a .env file first:
    echo   1. Copy .env.example to .env
    echo   2. Fill in your Azure resource values
    echo.
    echo Command: copy .env.example .env
    echo.
    pause
    exit /b 1
)

echo [1/4] Found .env file
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/4] Python is installed
echo.

REM Check if Azure CLI is installed
az --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Azure CLI is not installed
    echo Please install from https://learn.microsoft.com/cli/azure/install-azure-cli
    pause
    exit /b 1
)

echo [3/4] Azure CLI is installed
echo.

REM Check if authenticated
az account show >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Not authenticated with Azure CLI
    echo Please run: az login
    echo.
    set /p answer="Run 'az login' now? (y/n): "
    if /i "%answer%"=="y" (
        az login
    ) else (
        echo Please authenticate before running the application
        pause
        exit /b 1
    )
)

echo [4/4] Azure CLI authenticated
echo.

echo ========================================
echo Ready to start!
echo ========================================
echo.
echo Choose an option:
echo   1. Install dependencies (first time only)
echo   2. Verify setup (recommended)
echo   3. Run the ingestion pipeline
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
    echo.
    echo Next step: Run option 2 to verify your setup
    pause
) else if "%choice%"=="2" (
    echo.
    echo Verifying setup...
    python verify_setup.py
    if errorlevel 1 (
        echo.
        echo [ERROR] Setup verification failed
        echo Please fix the issues above before running the application
    ) else (
        echo.
        echo Setup verification completed!
    )
    pause
) else if "%choice%"=="3" (
    echo.
    echo Starting GPT-RAG Ingestion Pipeline...
    echo.
    echo The application will:
    echo   - Start a web server on http://localhost:80
    echo   - Run blob indexing immediately (if CRON_RUN_BLOB_INDEX is set)
    echo   - Schedule future runs based on your CRON expression
    echo.
    echo Press Ctrl+C to stop the application
    echo.
    pause
    python main.py
) else if "%choice%"=="4" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)
