param([Parameter(Mandatory=$true)][string]$Url)
$ErrorActionPreference = 'Stop'
$u = $Url.TrimEnd('/')
Write-Host "Checking $u ..."
$r = Invoke-WebRequest -Uri $u -UseBasicParsing -MaximumRedirection 5
if ($r.StatusCode -ne 200) { throw "Vercel returned HTTP $($r.StatusCode)." }
if ($r.Content -notmatch 'Sports Rehab AI') { Write-Warning 'HTTP 200 received, but the expected app title text was not found in the HTML shell.' }
Write-Host "Production URL responded with HTTP $($r.StatusCode)."
