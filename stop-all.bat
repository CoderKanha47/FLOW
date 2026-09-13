@echo off
REM Stops the Flow backend (8000) and frontend (3000) servers.
for %%P in (8000 3000) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo Killing PID %%A on port %%P
    taskkill /F /PID %%A >nul 2>&1
  )
)
echo All Flow servers stopped.