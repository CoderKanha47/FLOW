@echo off
REM Starts backend + frontend in two separate windows.
start "Flow Backend (8000)" cmd /k "%~dp0start-backend.bat"
start "Flow Frontend (3000)" cmd /k "%~dp0start-frontend.bat"
echo Both servers starting. Open http://127.0.0.1:3000/login in your browser.