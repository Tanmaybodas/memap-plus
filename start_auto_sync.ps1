# Auto Git Sync PowerShell Script for MeMap+
Write-Host "🚀 Starting Auto Git Sync for MeMap+" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📁 Repository: $(Get-Location)" -ForegroundColor Cyan
Write-Host "⏰ Checking for changes every 30 seconds" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the auto-sync" -ForegroundColor Yellow
Write-Host ""

# Run the auto-sync script
try {
    python auto_git_sync.py --interval 30
} catch {
    Write-Host "❌ Error running auto-sync: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
