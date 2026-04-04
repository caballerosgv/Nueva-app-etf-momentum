$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Resolve-Path (Join-Path $scriptDir "..")

Set-Location $repoDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "No se encontró .venv\Scripts\python.exe. Crea el entorno virtual primero."
}

& ".venv\Scripts\python.exe" "main.py"
