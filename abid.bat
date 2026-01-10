@echo off
set API_KEY=ollama
set BASE_URL=http://localhost:11434/v1
"%~dp0venv\Scripts\python" "%~dp0main.py" %*
