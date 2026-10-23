$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'No existe .venv. Ejecute: py -3.12 -m venv .venv'
}

& '.venv\Scripts\python.exe' -m pip install --upgrade pip
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.venv\Scripts\python.exe' -m pytest
& '.venv\Scripts\python.exe' 'scripts\generate_brand_assets.py'

$PyInstallerArgs = @(
    '--noconfirm', '--clean', '--windowed', '--name', 'CordonDeOro',
    '--collect-all', 'pyqtgraph', '--collect-all', 'supabase',
    '--add-data', 'assets;assets', 'main.py'
)
if (Test-Path -LiteralPath 'assets\icon.ico') {
    $PyInstallerArgs = @('--icon', 'assets\icon.ico') + $PyInstallerArgs
}
& '.venv\Scripts\python.exe' -m PyInstaller @PyInstallerArgs

$IsccCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Iscc) { throw 'Instale Inno Setup 6 para generar el instalador.' }
& $Iscc 'installer\CordonDeOro.iss'
Write-Host 'Instalador generado en output\CordonDeOro-Setup-0.1.0.exe'

