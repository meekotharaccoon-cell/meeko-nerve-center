Write-Host " AUTONOMOUS SYSTEM ACTIVATED" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Cyan

# Start the content generator
Write-Host "`n Starting content generation..." -ForegroundColor Yellow
python working_generator.py

Write-Host "`n SYSTEM READY FOR 24/7 OPERATION" -ForegroundColor Green
Write-Host " Content in: content\" -ForegroundColor Cyan
Write-Host " Runs daily at 6 AM automatically" -ForegroundColor Magenta
