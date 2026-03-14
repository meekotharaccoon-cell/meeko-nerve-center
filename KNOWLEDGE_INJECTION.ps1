$info = Read-Host "Enter the knowledge/fact you want to interweave into the system"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$entry = "[$timestamp] SolarPunk Wisdom: $info"
$entry | Out-File -FilePath "data/knowledge_bank.txt" -Append -Encoding utf8
Write-Host "🧠 Knowledge Interwoven. Run .\GUARD.ps1 to push to Cloud Brain." -ForegroundColor Green
