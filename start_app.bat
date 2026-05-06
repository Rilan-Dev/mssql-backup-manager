@echo off
echo Starting MSSQL Backup Manager...
echo.

:: Start Backend in a new window
start "MSSQL Backup Manager Backend" cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Start Frontend in a new window
start "MSSQL Backup Manager Frontend" cmd /k "cd frontend && npm run dev"

echo Backend API running at http://localhost:8000
echo Frontend UI running at http://localhost:5173
echo.
echo Application started successfully!
pause
