@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     ABID Agent - AI Coding Assistant      ║
echo  ║     Developed by Abid Raza                ║
echo  ║     Installation Script                   ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Get current directory
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

:: ============================================
:: CHECK PYTHON
:: ============================================
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please install Python 3.10+ from: https://python.org
    echo  Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)
echo       [OK] Python found

:: ============================================
:: CHECK/INSTALL OLLAMA
:: ============================================
echo [2/6] Checking Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo       Ollama not found!
    echo.
    echo  Please install Ollama manually:
    echo  1. Visit: https://ollama.ai
    echo  2. Download and install Ollama
    echo  3. Run this installer again
    echo.
    pause
    exit /b 1
) else (
    echo       [OK] Ollama found
)

:: ============================================
:: START OLLAMA SERVICE
:: ============================================
echo [3/6] Starting Ollama service...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %errorlevel% neq 0 (
    echo       Starting Ollama...
    start "" ollama serve
    timeout /t 5 /nobreak >nul
)
echo       [OK] Ollama service running

:: ============================================
:: CREATE VIRTUAL ENVIRONMENT
:: ============================================
echo [4/6] Setting up Python environment...
if not exist "%INSTALL_DIR%\venv" (
    echo       Creating virtual environment...
    python -m venv "%INSTALL_DIR%\venv"
)
echo       [OK] Virtual environment ready

:: Install dependencies
echo       Installing dependencies...
call "%INSTALL_DIR%\venv\Scripts\pip" install -r "%INSTALL_DIR%\requirements.txt" --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to install dependencies!
    echo  Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo       [OK] Dependencies installed

:: ============================================
:: PULL AI MODELS
:: ============================================
echo [5/6] Downloading AI models...
echo       This may take 10-15 minutes on first run...
echo.
echo       Pulling Qwen3.5:9B model (6.6 GB)...
echo       Best for 16GB RAM systems with vision support
echo.
ollama pull qwen3.5:9b
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to download model!
    echo  Please check your internet connection.
    echo.
    pause
    exit /b 1
)
echo       [OK] Model ready

:: ============================================
:: SETUP ABID COMMAND
:: ============================================
echo [6/6] Setting up 'abid' command...

:: Create PowerShell profile function
powershell -Command "$profileDir = Split-Path $PROFILE; if (!(Test-Path $profileDir)) { New-Item -Path $profileDir -ItemType Directory -Force | Out-Null }; if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force | Out-Null }; $content = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue; if ($content -notmatch 'function abid') { $abidFunc = \"`n# ABID Agent - AI Coding Assistant`nfunction abid {`n    `$env:API_KEY = 'ollama'`n    `$env:BASE_URL = 'http://localhost:11434/v1'`n    & '%INSTALL_DIR%\venv\Scripts\python.exe' '%INSTALL_DIR%\main.py' `$args`n}`n\"; Add-Content -Path $PROFILE -Value $abidFunc }" >nul 2>&1

echo       [OK] 'abid' command configured

:: ============================================
:: INSTALLATION COMPLETE
:: ============================================
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     Installation Complete!                ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  ABID Agent is now installed!
echo.
echo  ┌─────────────────────────────────────────────┐
echo  │  Quick Start:                               │
echo  │                                             │
echo  │  1. Open a NEW terminal window              │
echo  │  2. Type: abid                              │
echo  │  3. Start coding!                           │
echo  │                                             │
echo  │  Examples:                                  │
echo  │  - abid "hello"                             │
echo  │  - abid "create angular todo app"           │
echo  │  - abid --paste "fix this error"            │
echo  │                                             │
echo  │  For help: abid --help                      │
echo  │  Read: README.md                            │
echo  └─────────────────────────────────────────────┘
echo.
echo  Model: qwen3.5:9b (6.6 GB)
echo  Vision: Enabled
echo  Multi-Agent: Enabled
echo  Specialty: Angular Development
echo.
echo  Developed by Abid Raza
echo.
pause
