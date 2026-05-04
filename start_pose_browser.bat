@echo off
REM Quick start script for PAL Pose Browser
REM Run this to set up and start the pose browser

setlocal enabledelayedexpansion

echo.
echo ========================================
echo PAL Pose Browser - Setup & Start
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install fastapi uvicorn -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/3] Generating pose thumbnails...
echo        (This may take 1-2 minutes on first run)
python render_all_poses.py
if errorlevel 1 (
    echo WARNING: Thumbnail generation failed, but continuing...
)

echo.
echo [3/3] Starting Pose Browser server...
echo.
echo ========================================
echo Opening: http://localhost:8189
echo ========================================
echo.
echo Press CTRL+C to stop the server
echo.

python pose_browser_server.py

pause
