param([switch]$NoBackend)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = "$RootDir\frontend"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Shanbei Word Learning System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
$ActivateScript = "$RootDir\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
  & $ActivateScript
  Write-Host "[OK] Virtual env activated" -ForegroundColor Green
} else {
  Write-Host "[!] No virtual env found" -ForegroundColor Yellow
}

# Start backend
if (-not $NoBackend) {
  Write-Host "[..] Starting backend..." -ForegroundColor Yellow

  $job = Start-Job -Name "backend" -ScriptBlock {
    param($dir, $port)
    $activate = "$dir\Scripts\Activate.ps1"
    if (Test-Path $activate) { & $activate }
    Set-Location $dir
    uvicorn backend.src.main:app --host 127.0.0.1 --port $port --reload
  } -ArgumentList $RootDir, 8080

  Start-Sleep 4

  try {
    $null = Invoke-WebRequest "http://127.0.0.1:8080/docs" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Backend ready: http://127.0.0.1:8080" -ForegroundColor Green
  } catch {
    Write-Host "[!] Backend starting..." -ForegroundColor Yellow
  }
}

Write-Host ""

# Start frontend
Write-Host "[..] Starting frontend dev server..." -ForegroundColor Yellow
Push-Location $FrontendDir
pnpm dev
Pop-Location

# Cleanup
Write-Host "[..] Stopping backend..." -ForegroundColor Yellow
Get-Job -Name "backend" -ErrorAction SilentlyContinue | Stop-Job | Remove-Job
Write-Host "[OK] Stopped" -ForegroundColor Green
