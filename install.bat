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

:: ============================================
:: CHECK PYTHON
:: ============================================
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please install Python from: https://python.org
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
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo       Ollama not found. Downloading Ollama...
    echo.
    
    :: Download Ollama installer
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'"
    
    if exist "%TEMP%\OllamaSetup.exe" (
        echo       Installing Ollama...
        start /wait "" "%TEMP%\OllamaSetup.exe"
        del "%TEMP%\OllamaSetup.exe"
        
        :: Wait for Ollama to be available
        timeout /t 5 /nobreak >nul
        
        ollama --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo.
            echo  [ERROR] Ollama installation failed!
            echo  Please install manually from: https://ollama.ai
            echo.
            pause
            exit /b 1
        )
        echo       [OK] Ollama installed successfully
    ) else (
        echo.
        echo  [ERROR] Failed to download Ollama!
        echo  Please install manually from: https://ollama.ai
        echo.
        pause
        exit /b 1
    )
) else (
    echo       [OK] Ollama found
)

:: ============================================
:: START OLLAMA SERVICE
:: ============================================
echo [3/6] Starting Ollama service...
:: Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %errorlevel% neq 0 (
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)
echo       [OK] Ollama service running

:: ============================================
:: CREATE VIRTUAL ENVIRONMENT
:: ============================================
echo [4/6] Setting up Python environment...
if not exist "%INSTALL_DIR%\venv" (
    python -m venv "%INSTALL_DIR%\venv"
)
echo       [OK] Virtual environment ready

:: Install dependencies
echo       Installing dependencies...
call "%INSTALL_DIR%\venv\Scripts\pip" install -r "%INSTALL_DIR%\requirements.txt" -q
echo       [OK] Dependencies installed

:: ============================================
:: PULL AI MODELS
:: ============================================
echo [5/6] Downloading AI models...
echo       This may take several minutes on first run...
echo.
echo       Pulling coding model (qwen2.5-coder:7b)...
ollama pull qwen2.5-coder:7b
echo       [OK] Coding model ready
echo.
echo       Pulling vision model (llava:7b)...
ollama pull llava:7b
echo       [OK] Vision model ready

:: ============================================
:: SETUP ABID COMMAND
:: ============================================
echo [6/6] Setting up 'abid' command...

:: Create PowerShell script to add to profile
set "PS_SCRIPT=%TEMP%\add_abid.ps1"

echo $profileDir = Split-Path $PROFILE > "%PS_SCRIPT%"
echo if (!(Test-Path $profileDir)) { New-Item -Path $profileDir -ItemType Directory -Force ^| Out-Null } >> "%PS_SCRIPT%"
echo if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force ^| Out-Null } >> "%PS_SCRIPT%"
echo $content = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue >> "%PS_SCRIPT%"
echo if ($content -notmatch 'function abid') { >> "%PS_SCRIPT%"
echo     $abidFunc = @' >> "%PS_SCRIPT%"
echo. >> "%PS_SCRIPT%"
echo # ABID - AI Coding Assistant >> "%PS_SCRIPT%"
echo function abid { >> "%PS_SCRIPT%"
echo     $env:API_KEY = "ollama" >> "%PS_SCRIPT%"
echo     $env:BASE_URL = "http://localhost:11434/v1" >> "%PS_SCRIPT%"
echo     ^& "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\main.py" $args >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"
echo '@ >> "%PS_SCRIPT%"
echo     Add-Content -Path $PROFILE -Value $abidFunc >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" >nul 2>&1
del "%PS_SCRIPT%" >nul 2>&1

echo       [OK] 'abid' command configured

:: ============================================
:: INSTALLATION COMPLETE - START ABID
:: ============================================
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     Installation Complete!                ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  Starting ABID AI Assistant...
echo.
echo  ┌─────────────────────────────────────────────┐
echo  │  TIP: After this session, open a NEW       │
echo  │  terminal and type 'abid' anywhere!        │
echo  └─────────────────────────────────────────────┘
echo.

:: Set environment and start ABID
set API_KEY=ollama
set BASE_URL=http://localhost:11434/v1
"%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\main.py"
