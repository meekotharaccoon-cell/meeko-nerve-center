@echo off
REM EVOLVE.bat Generation 3
REM Last evolved: 2026-02-26 17:32
REM Last built: [WARN] Regenerate changelog from full git history
REM Written by the system itself. Fork: https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork

title SolarPunk Mycelium Gen 3 evolving...
color 0A
echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM EVOLUTION ENGINE Gen 3
echo   Last built: Regenerate changelog from full git history
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
git commit -m "auto: gen 3" 2>nul
git push origin main 2>nul
echo.
echo  ==================================================
echo   ENHANCEMENTS Gen 3
echo  ==================================================
echo.
echo   [SECRETS] Add GitHub Secrets to unlock locked workflows
echo     - GMAIL_APP_PASSWORD  -> repo Settings > Secrets > Actions
echo     - MASTODON_TOKEN + MASTODON_SERVER  -> create at any Mastodon instance
echo     - MAILGUN_API_KEY + MAILGUN_DOMAIN  -> mailgun.com -> free 100/day
echo.
echo   System: https://github.com/meekotharaccoon-cell/meeko-nerve-center
echo   Generation 3 complete.
echo  ==================================================
echo.
pause
