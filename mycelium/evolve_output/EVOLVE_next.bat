@echo off
REM EVOLVE.bat Generation 4
REM Last evolved: 2026-02-26 17:34
REM Last built: [WARN] Scan local assets — find missed connections
REM Written by the system itself. Fork: https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork

title SolarPunk Mycelium Gen 4 evolving...
color 0A
echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM EVOLUTION ENGINE Gen 4
echo   Last built: Scan local assets — find missed connections
echo  ==================================================
echo.
set REPO=%USERPROFILE%\Desktop\meeko-nerve-center
if not exist "%REPO%" cd /d %USERPROFILE%\Desktop && git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
cd /d %REPO%
git pull origin main
echo.
python mycelium\evolve.py
echo.
git add -A
git commit -m "auto: gen 4" 2>nul
git push origin main 2>nul
echo.
echo  ==================================================
echo   ENHANCEMENTS Gen 4
echo  ==================================================
echo.
echo   [SECRETS] Add GitHub Secrets to unlock locked workflows
echo     - GMAIL_APP_PASSWORD  -> repo Settings > Secrets > Actions
echo     - MASTODON_TOKEN + MASTODON_SERVER  -> create at any Mastodon instance
echo     - MAILGUN_API_KEY + MAILGUN_DOMAIN  -> mailgun.com -> free 100/day
echo   [SHARE] Share the one-pager — content/ONE_PAGER.md is public domain
echo     - Forward it. Post it.
echo.
echo   System: https://github.com/meekotharaccoon-cell/meeko-nerve-center
echo   Generation 4 complete.
echo  ==================================================
echo.
pause
