@echo off
echo.
echo ================================================================
echo   MEEKO LOCAL SERVER -- Desktop GitHub Replica
echo   Your pages running LOCALLY, no internet needed.
echo ================================================================
echo.

set REPO=%~dp0

:: Find Python
set PYCMD=
where python >nul 2>&1 && set PYCMD=python
if "%PYCMD%"=="" where python3 >nul 2>&1 && set PYCMD=python3

if "%PYCMD%"=="" (
    echo Python not found. Install from python.org
    pause
    exit /b 1
)

echo Starting server at http://localhost:8888
echo.
echo  Your pages:
echo   http://localhost:8888/spawn.html
echo   http://localhost:8888/proliferator.html
echo   http://localhost:8888/revenue.html
echo   http://localhost:8888/dashboard.html
echo   http://localhost:8888/app.html
echo.
echo Press Ctrl+C to stop the server.
echo.

:: Open browser
timeout /t 1 /nobreak >nul
powershell -Command "Start-Process 'http://localhost:8888'"

:: Start server
%PYCMD% -m http.server 8888 --directory "%REPO%"
