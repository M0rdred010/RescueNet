@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"
set "APP_FILE=%ROOT_DIR%app.py"
set "REQ_FILE=%ROOT_DIR%requirements.txt"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment not found: %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%APP_FILE%" (
    echo [ERROR] App file not found: %APP_FILE%
    pause
    exit /b 1
)

if exist "%REQ_FILE%" (
    echo Installing or updating project dependencies...
    "%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Starting Streamlit UI...
"%PYTHON_EXE%" -m streamlit run "%APP_FILE%"

endlocal
