@echo off
echo Installing Python dependencies for Minecraft Server Manager...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not available
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error: Failed to install some packages
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo You can now run the Minecraft Server Manager with: python minecraft_server_manager.py
echo.
pause
