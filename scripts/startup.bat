@echo off
echo Starting Alchemist AI Full-Stack...

REM Start Backend
start cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Start Frontend
start cmd /k "cd frontend && npm run dev"

echo Both services are starting...
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
