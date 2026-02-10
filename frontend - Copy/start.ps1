# Velora Frontend Startup Script
# This script starts the frontend dev server in a new PowerShell window that stays open

$FrontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting Velora Frontend Server..." -ForegroundColor Green
Write-Host "Frontend path: $FrontendPath" -ForegroundColor Cyan

# Check if node_modules exists, if not, install dependencies
if (-not (Test-Path "$FrontendPath\node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    cd $FrontendPath
    npm install
}

# Start the server in a new PowerShell window
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$FrontendPath'; Write-Host 'Velora Frontend Development Server' -ForegroundColor Green; Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow; npm run dev"

Write-Host ""
Write-Host "Server started in new window!" -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open in browser: http://localhost:5173" -ForegroundColor Yellow
