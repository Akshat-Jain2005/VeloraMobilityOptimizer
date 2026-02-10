# Velora Quick Start Script for Windows PowerShell
# This script starts the Velora backend server

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  VELORA MOBILITY OPTIMIZER - Quick Start" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "$PSScriptRoot\backend"

Write-Host "Starting server on http://localhost:3000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

node server.js
