@echo off
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     ABID - AI Coding Assistant            ║
echo  ║     Installation Script                   ║
echo  ╚═══════════════════════════════════════════╝
echo.

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
if not exist "venv" (
    python -m venv venv
)
echo [OK] Virtual environment ready

:: Install dependencies
echo.
echo [SETUP] Installing dependencies...
call venv\Scripts\pip install -r requirements.txt -q
echo [OK] Dependencies installed

:: Pull Ollama model
echo.
echo [SETUP] Pulling AI model (glm-4.7:cloud)...
ollama pull glm-4.7:cloud
echo [OK] Model ready

:: Create bin directory
if not exist "%USERPROFILE%\bin" mkdir "%USERPROFILE%\bin"

:: Create abid.bat in user bin
echo @echo off > "%USERPROFILE%\bin\abid.bat"
echo set API_KEY=ollama >> "%USERPROFILE%\bin\abid.bat"
echo set BASE_URL=http://localhost:11434/v1 >> "%USERPROFILE%\bin\abid.bat"
echo "%~dp0venv\Scripts\python" "%~dp0main.py" %%* >> "%USERPROFILE%\bin\abid.bat"

:: Also create in current directory
echo @echo off > abid.bat
echo set API_KEY=ollama >> abid.bat
echo set BASE_URL=http://localhost:11434/v1 >> abid.bat
echo "%%~dp0venv\Scripts\python" "%%~dp0main.py" %%* >> abid.bat

:: Add to PATH
echo.
echo [SETUP] Adding to system PATH...
setx PATH "%PATH%;%USERPROFILE%\bin" >nul 2>&1

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     Installation Complete!                ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  Usage:
echo    1. Open a NEW terminal
echo    2. Go to any project folder
echo    3. Type: abid
echo.
echo  Examples:
echo    abid "list all files"
echo    abid "add dark mode to this project"
echo    abid "fix the login bug"
echo.
pause
