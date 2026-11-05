param([switch]$LocalModel)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Install and start Docker Desktop first.'
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker is not ready. Start Docker Desktop and retry.' }
if (!(Test-Path -LiteralPath '.env')) {
    $template = if ($LocalModel) { '.env.ollama.example' } else { '.env.example' }
    Copy-Item -LiteralPath $template -Destination '.env'
    Write-Host 'Created .env. Local models: ollama pull qwen3:4b; ollama pull bge-m3'
    if (!$LocalModel) {
        Write-Host 'Fill API credentials in .env, then run this script again.'
        notepad .env
        exit 0
    }
} elseif ($LocalModel) {
    Write-Host 'Keeping your existing .env. To use Ollama, copy settings from .env.ollama.example.'
}
if (Test-Path -LiteralPath 'clinic.db' -PathType Container) {
    throw 'clinic.db is a directory, but must be a SQLite file. Back it up and fix it before starting.'
}
if (!(Test-Path -LiteralPath 'clinic.db')) {
    New-Item -ItemType File -Path 'clinic.db' | Out-Null
}
docker compose up -d --build --force-recreate
if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Read the Docker error above.' }
Write-Host 'Web: http://localhost:8000  Admin: http://localhost:8000/admin/login'
Write-Host 'Check models: docker compose exec clinic-agent python scripts/check_models.py'
