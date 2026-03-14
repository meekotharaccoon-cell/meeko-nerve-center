Write-Host "--- MEEKO NERVE CENTER: BOOTSTRAP ---" -ForegroundColor Cyan
git pull origin main
if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "Virtual Environment Created." -ForegroundColor Green
}
.\venv\Scripts\activate
pip install -r requirements.txt
python mycelium/GMAIL_INTAKE.py
python mycelium/CAPABILITY_SCANNER.py
Write-Host "System Linked & Operational." -ForegroundColor Green
