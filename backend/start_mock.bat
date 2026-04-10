@echo off
cd /d "%~dp0"
echo [INFO] Backend BookTime - Mode MOCK (sans MongoDB)
echo [INFO] URL: http://localhost:8001
echo.
set RAILWAY_MONGODB_MOCK=true
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
pause
