$info = Read-Host "Enter the knowledge/fact you want to interweave into the system"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$entry = "[$timestamp] SolarPunk Wisdom: $info"
# Use [System.IO.File]::WriteAllLines to ensure NO-BOM UTF8
[System.IO.File]::AppendAllLines("$PWD\data\knowledge_bank.txt", [string[]]$entry)
Write-Host "?? Knowledge Interwoven. Run .\GUARD.ps1 to push to Cloud Brain." -ForegroundColor Green
