@echo off
REM Velora Quick Start Script for Windows
REM This script starts the Velora backend server

echo ================================================
echo   VELORA MOBILITY OPTIMIZER - Quick Start
echo ================================================
echo.

cd /d "%~dp0backend"

echo Starting server on http://localhost:3000...
echo Press Ctrl+C to stop the server
echo.

node server.js
