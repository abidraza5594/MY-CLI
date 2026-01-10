@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     ABID - AI Coding Assistant            ║
echo  ║     Installation Script                   ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Get current directory
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

:: Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not installed!
    echo Please install Ollama from https://ollama.ai
    pause
    exit /b 1
)
echo [OK] Ollama found

:: Create virtual environment
echo.
echo [SETUP] Creating virtual environment...
if not exist "%INSTALL_DIR%\venv" (
    python -m venv "%INSTALL_DIR%\venv"
)
echo [OK] Virtual environment ready

:: Install dependencies
echo.
echo [SETUP] Installing dependencies...
call "%INSTALL_DIR%\venv\Scripts\pip" install -r "%INSTALL_DIR%\requirements.txt" -q
echo [OK] Dependencies installed

:: Pull Ollama model
echo.
echo [SETUP] Pulling AI model (glm-4.7:cloud)...
echo         This may take a few minutes...
ollama pull glm-4.7:cloud
echo [OK] Model ready

:: Create PowerShell profile with abid function
echo.
echo [SETUP] Adding 'abid' command to PowerShell...

:: Create PowerShell script to add to profile
set "PS_SCRIPT=%TEMP%\add_abid.ps1"
echo $profileDir = Split-Path $PROFILE > "%PS_SCRIPT%"
echo if (!(Test-Path $profileDir)) { New-Item -Path $profileDir -ItemType Directory -Force } >> "%PS_SCRIPT%"
echo if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force } >> "%PS_SCRIPT%"
echo $content = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue >> "%PS_SCRIPT%"
echo if ($content -notmatch 'function abid') { >> "%PS_SCRIPT%"
echo     $abidFunc = @" >> "%PS_SCRIPT%"
echo. >> "%PS_SCRIPT%"
echo # ABID - AI Coding Assistant >> "%PS_SCRIPT%"
echo function abid { >> "%PS_SCRIPT%"
echo     `$env:API_KEY = "ollama" >> "%PS_SCRIPT%"
echo     `$env:BASE_URL = "http://localhost:11434/v1" >> "%PS_SCRIPT%"
echo     ^& "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\main.py" `$args >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"
echo "@ >> "%PS_SCRIPT%"
echo     Add-Content -Path $PROFILE -Value $abidFunc >> "%PS_SCRIPT%"
echo     Write-Host '[OK] abid command added to PowerShell profile' >> "%PS_SCRIPT%"
echo } else { >> "%PS_SCRIPT%"
echo     Write-Host '[OK] abid command already exists in profile' >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%"

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     Installation Complete!                ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  ┌─────────────────────────────────────────────┐
echo  │  IMPORTANT: Close this terminal and        │
echo  │  open a NEW PowerShell window to use       │
echo  │  the 'abid' command.                       │
echo  └─────────────────────────────────────────────┘
echo.
echo  Usage Examples:
echo.
echo    abid                          - Start interactive mode
echo    abid "list all files"         - Run with prompt
echo    abid "add login feature"      - Add features to project
echo    abid "fix the bug in app.js"  - Fix bugs
echo.
echo  Just type 'abid' in any folder to start!
echo.
pause
