@echo off
REM EVOLVE.bat Generation 12
REM Last evolved: 2026-02-27 05:35
REM Last built: [WARN] Rebuild knowledge library index
REM Written by the system itself. Fork: https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork

title SolarPunk Mycelium Gen 12 evolving...
color 0A
echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM EVOLUTION ENGINE Gen 12
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
git commit -m "auto: gen 12" 2>nul
git push origin main 2>nul
echo.
echo  ==================================================
echo   ENHANCEMENTS Gen 12
echo  ==================================================
echo.
echo   [SECRETS] Add GitHub Secrets to unlock locked workflows
echo     - GMAIL_APP_PASSWORD  -> repo Settings > Secrets > Actions
echo     - MASTODON_TOKEN + MASTODON_SERVER  -> create at any Mastodon instance
echo     - MAILGUN_API_KEY + MAILGUN_DOMAIN  -> mailgun.com -> free 100/day
echo   [SHARE] Share the one-pager — content/ONE_PAGER.md is public domain
echo     - Forward it. Post it.
echo   [REDDIT] Post to Reddit communities
echo     - r/selfhosted -> mycelium/reddit_posts.md
echo     - r/solarpunk -> mycelium/reddit_posts.md
echo   [DEVTO] Publish Dev.to article — mycelium/devto_article.md is ready
echo     - Go to dev.to > New Post > paste it
echo   [DOMAIN] Consider solarpunkmycelium.org (~$8/yr) for email deliverability
echo     - porkbun.com or namecheap.com
echo.
echo   System: https://github.com/meekotharaccoon-cell/meeko-nerve-center
echo   Generation 12 complete.
echo  ==================================================
echo.
pause
