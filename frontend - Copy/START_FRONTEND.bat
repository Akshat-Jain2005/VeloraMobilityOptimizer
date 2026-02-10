@echo off
REM Velora Frontend Startup Script
REM Double-click this file to start the frontend dev server

echo Starting Velora Frontend Server...
echo.

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "start.ps1"

echo.
pause
