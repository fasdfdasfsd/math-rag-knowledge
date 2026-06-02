# Math Adventure World — Windows Dev Startup
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"

Write-Host "=== Starting backend ===" -ForegroundColor Green
$backend = Start-Process -NoNewWindow -PassThru -FilePath "uv" -ArgumentList "run","uvicorn","src.main:app","--reload","--port","8000"

Write-Host "=== Starting frontend ===" -ForegroundColor Green
$frontend = Start-Process -NoNewWindow -PassThru -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory "frontend"

Write-Host ""
Write-Host "Backend:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow

try { Wait-Process -Id $backend.Id, $frontend.Id } finally {
    Stop-Process -Id $backend.Id, $frontend.Id -Force -ErrorAction SilentlyContinue
}
