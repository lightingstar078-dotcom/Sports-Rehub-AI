@echo off
setlocal
cd /d %~dp0\..
start "Sports Rehab AI Backend" cmd /k "cd backend && py -3.13 -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python main.py"
start "Sports Rehab AI Frontend" cmd /k "cd frontend && npm install && npm run dev"
endlocal
