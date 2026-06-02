@echo off
REM XAUUSD God Bot - One-Command Runner for Windows
REM Usage: start_bot.bat

echo ==========================================
echo   XAUUSD GOD BOT - Starting...
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM Run the bot
python run_all.py

echo ==========================================
echo   Bot execution finished
echo ==========================================
pause