@echo off
REM EVOLVE.bat Generation 2
REM Last evolved: 2026-02-26 17:29
REM Last built: [WARN] Rebuild knowledge library index
REM Written by the system itself. Fork: https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork

title SolarPunk Mycelium Gen 2 evolving...
color 0A
echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM EVOLUTION ENGINE Gen 2
echo   Last built: Rebuild knowledge library index
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
git commit -m "auto: gen 2" 2>nul
git push origin main 2>nul
echo.
echo  ==================================================
echo   ENHANCEMENTS Gen 2
echo  ==================================================
echo.
echo   [SECRETS] Add GitHub Secrets to unlock locked workflows
echo     - GMAIL_APP_PASSWORD  -> repo Settings > Secrets > Actions
echo     - MASTODON_TOKEN + MASTODON_SERVER  -> create at any Mastodon instance
echo     - MAILGUN_API_KEY + MAILGUN_DOMAIN  -> mailgun.com -> free 100/day
echo   [FIRST] First run! Post to Hacker News today
echo     - SHOW_HN.md is ready to copy-paste
echo.
echo   System: https://github.com/meekotharaccoon-cell/meeko-nerve-center
echo   Generation 2 complete.
echo  ==================================================
echo.
pause
