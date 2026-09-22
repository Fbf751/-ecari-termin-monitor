# Runs the eCARI monitor once and pushes an updated state/found.json if a
# new appointment was found. Invoked every 10 minutes by a Windows
# Scheduled Task (see README.md "Lokal laufen lassen") - this machine's
# real IP reaches portal.stva.zh.ch, unlike GitHub Actions' datacenter IPs.

Set-Location -Path (Join-Path $PSScriptRoot "..")

python -m bot.monitor

git add state/found.json
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "Status aktualisieren (lokal)" | Out-Null
    git push | Out-Null
}
