$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'Se requiere Node.js 24 o posterior: https://nodejs.org/'
}

& npm.cmd ci
& npm.cmd audit --audit-level=moderate
& npm.cmd test
& npm.cmd run dist

$Package = Get-Content -LiteralPath 'package.json' -Raw | ConvertFrom-Json
Write-Host "Instalador Electron generado en release\CordonDeOro-Setup-$($Package.version).exe"

