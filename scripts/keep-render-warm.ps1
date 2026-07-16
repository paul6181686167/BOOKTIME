# Ping Render toutes les 14 min pour éviter le cold start (plan gratuit).
# Lancer dans une fenêtre PowerShell dédiée pendant que tu testes booktime.vercel.app

$Url = $env:BOOKTIME_RENDER_URL
if (-not $Url) {
    $Url = "https://booktime-uo15.onrender.com/ping"
}
Write-Host "Keep-warm : $Url (Ctrl+C pour arrêter)" -ForegroundColor Cyan

while ($true) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 60
        Write-Host "$(Get-Date -Format 'HH:mm:ss') OK $($r.StatusCode)"
    } catch {
        Write-Host "$(Get-Date -Format 'HH:mm:ss') ECHEC $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 840
}
