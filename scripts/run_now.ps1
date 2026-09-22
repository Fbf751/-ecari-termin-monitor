# Manual "check right now" entry point with a console window that stays
# open so you can see what happened, instead of the silent scheduled run.

Set-Location -Path (Join-Path $PSScriptRoot "..")

Write-Host "eCARI Monitor - prüfe jetzt..." -ForegroundColor Cyan
Write-Host ""

python -m bot.monitor

git add state/found.json
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "Status aktualisieren (lokal)" | Out-Null
    git push | Out-Null
}

Write-Host ""
Read-Host "Fertig - Enter zum Schliessen"
