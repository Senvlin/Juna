@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Shanbei Word Learning System
echo ========================================
echo.

if exist "Scripts\activate.bat" (
    call Scripts\activate.bat
    echo [OK] Virtual env activated
) else (
    echo [!] No virtual env found
)

echo [..] Starting backend...
start "Shanbei-Backend" cmd /c "Scripts\python.exe -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8080 --reload"
timeout /t 5 /nobreak >nul
echo [OK] Backend ready: http://127.0.0.1:8080
echo.

echo [..] Starting frontend...
cd frontend
call pnpm dev

echo.
echo [..] Stopping backend...
taskkill /f /fi "WINDOWTITLE eq Shanbei-Backend" >nul 2>&1
echo [OK] Stopped
pause
