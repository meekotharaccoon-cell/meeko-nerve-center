@echo off
setlocal enabledelayedexpansion
color 0A

echo.
echo ################################################################
echo #
echo #   MEEKO MYCELIUM -- MASTER RUN
echo #   Everything. All of it. In order.
echo #
echo ################################################################
echo.

:: Find Python
set PYCMD=
where python >nul 2>&1 && set PYCMD=python
if "%PYCMD%"=="" where python3 >nul 2>&1 && set PYCMD=python3
if "%PYCMD%"=="" (
    echo [ERROR] Python not found. Install from python.org then re-run.
    echo         Make sure to check 'Add Python to PATH' during install.
    pause
    exit /b 1
)
echo [OK] Python found: %PYCMD%

:: Find repo
set REPO=
if exist "%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center" (
    set REPO=%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center
) else if exist "%USERPROFILE%\Desktop\meeko-nerve-center" (
    set REPO=%USERPROFILE%\Desktop\meeko-nerve-center
) else if exist "%USERPROFILE%\meeko-nerve-center" (
    set REPO=%USERPROFILE%\meeko-nerve-center
)

if "%REPO%"=="" (
    echo [!] Repo not found. Downloading now...
    where git >nul 2>&1
    if errorlevel 1 (
        echo [!] Git not installed. Downloading ZIP instead...
        mkdir "%USERPROFILE%\Desktop\UltimateAI_Master" 2>nul
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/meekotharaccoon-cell/meeko-nerve-center/archive/refs/heads/main.zip' -OutFile '%TEMP%\mnc.zip'"
        powershell -Command "Expand-Archive -Path '%TEMP%\mnc.zip' -DestinationPath '%USERPROFILE%\Desktop\UltimateAI_Master' -Force"
        ren "%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center-main" "meeko-nerve-center"
    ) else (
        mkdir "%USERPROFILE%\Desktop\UltimateAI_Master" 2>nul
        git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center.git "%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center"
    )
    set REPO=%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center
)

echo [OK] Repo: %REPO%
cd /d "%REPO%"
echo.

:: ============================================================
:: 1. GIT PULL
:: ============================================================
echo [1/12] Pulling latest from GitHub...
where git >nul 2>&1
if not errorlevel 1 (
    git pull origin main
    echo [OK] Repo updated.
) else (
    echo [!] Git not installed -- skipping pull.
)
echo.

:: ============================================================
:: 2. INSTALL DEPENDENCIES
:: ============================================================
echo [2/12] Installing Python dependencies...
%PYCMD% -m pip install requests flask websockets paho-mqtt gitpython --quiet
echo [OK] Dependencies checked.
echo.

:: ============================================================
:: 3. CLEANUP AND BRIDGE
:: ============================================================
echo [3/12] Running Cleanup and Bridge...
if exist "%REPO%\CLEANUP_AND_BRIDGE.py" (
    %PYCMD% "%REPO%\CLEANUP_AND_BRIDGE.py"
) else (
    echo [!] CLEANUP_AND_BRIDGE.py not found
)
echo.

:: ============================================================
:: 4. WIRING HUB
:: ============================================================
echo [4/12] Running Wiring Hub (connecting all layers)...
if exist "%REPO%\mycelium\wiring_hub.py" (
    %PYCMD% "%REPO%\mycelium\wiring_hub.py"
) else (
    echo [!] wiring_hub.py not found
)
echo.

:: ============================================================
:: 5. SPACE BRIDGE
:: ============================================================
echo [5/12] Running Space Bridge (ISS + NASA data)...
if exist "%REPO%\mycelium\space_bridge.py" (
    %PYCMD% "%REPO%\mycelium\space_bridge.py"
) else (
    echo [!] space_bridge.py not found
)
echo.

:: ============================================================
:: 6. NETWORK NODE
:: ============================================================
echo [6/12] Running Network Node...
if exist "%REPO%\mycelium\network_node.py" (
    %PYCMD% "%REPO%\mycelium\network_node.py"
) else (
    echo [!] network_node.py not found
)
echo.

:: ============================================================
:: 7. UPDATE STATE
:: ============================================================
echo [7/12] Updating system state (CLAUDE_CONTEXT.md)...
if exist "%REPO%\mycelium\update_state.py" (
    %PYCMD% "%REPO%\mycelium\update_state.py"
) else (
    echo [!] update_state.py not found
)
echo.

:: ============================================================
:: 8. BUILD MCP CONFIG
:: ============================================================
echo [8/12] Building MCP Config (wire Claude Desktop)...
if exist "%REPO%\BUILD_MCP_CONFIG.py" (
    %PYCMD% "%REPO%\BUILD_MCP_CONFIG.py"
) else (
    echo [!] BUILD_MCP_CONFIG.py not found
)
echo.

:: ============================================================
:: 9. PHONE PACKAGE
:: ============================================================
echo [9/12] Creating phone package...
if exist "%REPO%\PHONE_PACKAGE.py" (
    %PYCMD% "%REPO%\PHONE_PACKAGE.py"
) else (
    echo [!] PHONE_PACKAGE.py not found
)
echo.

:: ============================================================
:: 10. LOCAL SERVER (desktop GitHub replica)
:: ============================================================
echo [10/12] Starting local web server (desktop GitHub replica)...
echo         Your pages will be live at http://localhost:8888
echo         Opening in browser...
powershell -Command "Start-Process 'http://localhost:8888'" 2>nul
start /min cmd /c "%PYCMD% -m http.server 8888 --directory \"%REPO%\"" 
echo [OK] Local server started at http://localhost:8888
echo.

:: ============================================================
:: 11. FIX BRAVE
:: ============================================================
echo [11/12] Fixing Brave browser...
if exist "%REPO%\FIX_BRAVE.ps1" (
    powershell -ExecutionPolicy Bypass -File "%REPO%\FIX_BRAVE.ps1"
) else (
    echo [!] FIX_BRAVE.ps1 not found
)
echo.

:: ============================================================
:: 12. GRAND SETUP WIZARD
:: ============================================================
echo [12/12] Opening Grand Setup Wizard at http://localhost:7776...
if exist "%REPO%\GRAND_SETUP_WIZARD.py" (
    start /min cmd /c "%PYCMD% \"%REPO%\GRAND_SETUP_WIZARD.py\""
    timeout /t 2 /nobreak >nul
    powershell -Command "Start-Process 'http://localhost:7776'"
    echo [OK] Setup Wizard running -- fill in your API keys.
) else (
    echo [!] GRAND_SETUP_WIZARD.py not found
)
echo.

:: ============================================================
:: FINAL SUMMARY
:: ============================================================
echo ################################################################
echo #   MASTER RUN COMPLETE
echo ################################################################
echo.
echo   What's now running:
echo   - Local web server:  http://localhost:8888  (your pages, offline)
echo   - Setup Wizard:      http://localhost:7776  (API keys)
echo   - All mycelium scripts ran
echo   - MCP config updated (restart Claude Desktop)
echo   - Phone package: Desktop\meeko_phone_package.zip
echo.
echo   NEXT STEPS:
echo   1. RESTART CLAUDE DESKTOP (MCP config changed)
echo   2. Fill API keys at http://localhost:7776
echo   3. Add GMAIL_APP_PASSWORD to GitHub Secrets:
echo      github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets
echo   4. Email meeko_phone_package.zip to your phone
echo.
echo   GITHUB PAGES FIX:
echo   Go to: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/pages
echo   Set source: Deploy from branch, branch: main, folder: / (root)
echo   Save. Pages will be live in ~2 minutes.
echo.
pause
