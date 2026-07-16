# Lance l'extraction Wikidata incrementale (nouvelles franchises + hubs P179).
# Resumable : relancer ce script reprend où le checkpoint s'est arrêté.
# Duree estimee : 30 min a 2 h selon QLever (seulement les NOUVEAUX QIDs en passe 2).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Booktime : extraction Wikidata incrementale ===" -ForegroundColor Cyan
Write-Host "Repertoire : $Root"
Write-Host "Log : wikidata_incremental_extract.log"
Write-Host ""

python extract_wikidata_series.py --incremental 2>&1 | Tee-Object -FilePath "wikidata_incremental_extract.log"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Extraction interrompue (code $LASTEXITCODE). Relancez ce script pour reprendre." -ForegroundColor Yellow
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Termine. Redemarrez le backend pour recharger l'index en RAM." -ForegroundColor Green
