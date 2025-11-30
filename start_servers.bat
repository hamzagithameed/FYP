@echo off
echo ========================================
echo Starting Handwriting Generation App
echo ========================================
echo.

echo [1/2] Starting Backend API...
start "Backend API" cmd /k "cd /d %~dp0 && python -m uvicorn api.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0 && npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend API: http://127.0.0.1:8000
echo Frontend:    http://localhost:5173/
echo API Docs:    http://127.0.0.1:8000/docs
echo.
echo Press any key to open the app in your browser...
pause >nul

start http://localhost:5173/

echo.
echo Servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
