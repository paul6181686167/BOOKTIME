# Démarre Booktime en LOCAL (backend + front, Mongo MOCK, Wikidata sur disque)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$root\wikidata_series_db.json")) {
    Write-Host "ERREUR: wikidata_series_db.json introuvable à la racine BOOKTIME-main." -ForegroundColor Red
    exit 1
}

$envLocal = "$root\backend\.env.local"
$envExample = "$root\backend\.env.local.example"
if (-not (Test-Path $envLocal)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envLocal
        Write-Host "Créé backend\.env.local (mode MOCK)" -ForegroundColor Yellow
    } else {
        @"
RAILWAY_MONGODB_MOCK=true
ENVIRONMENT=development
"@ | Set-Content -Path $envLocal -Encoding UTF8
    }
}

Write-Host ""
Write-Host "=== Booktime LOCAL ===" -ForegroundColor Green
Write-Host "Backend  : http://localhost:8001  (Mongo MOCK, Wikidata 532k séries)"
Write-Host "Frontend : http://localhost:3000"
Write-Host "Guide    : $root\TESTER_LOCAL.md"
Write-Host ""

Write-Host "Démarrage backend…" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\backend'; `$env:RAILWAY_MONGODB_MOCK='true'; python server.py"
)

Start-Sleep -Seconds 6

Write-Host "Démarrage frontend…" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\frontend'; npm start"
)

Write-Host ""
Write-Host "Ouvre http://localhost:3000 dans le navigateur." -ForegroundColor Green
Write-Host "Pas de veille Render : tout tourne sur ta machine." -ForegroundColor Green
