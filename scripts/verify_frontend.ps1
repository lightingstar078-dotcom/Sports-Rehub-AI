$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..' 'frontend')
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm is not installed or not on PATH.' }
Write-Host 'Installing frontend dependencies...'
npm install
Write-Host 'Running production build...'
npm run build
if (-not (Test-Path 'dist/index.html')) { throw 'Vite build completed without dist/index.html.' }
Write-Host 'Frontend production build verified: dist/index.html exists.'
