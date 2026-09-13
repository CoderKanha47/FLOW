@echo off
REM Starts the Flow frontend (Next.js) on http://127.0.0.1:3000
cd /d "%~dp0frontend"
if not exist "node_modules" (
  echo Installing dependencies...
  call npm install
)
call npm run dev