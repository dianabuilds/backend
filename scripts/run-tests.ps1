param(
    [Parameter(Position=0)][string]$Pattern
)

if (-not (Test-Path env:APP_ENV)) {
    $env:APP_ENV = 'test'
}
if (-not (Test-Path env:APP_ADMIN_API_KEY)) {
    $env:APP_ADMIN_API_KEY = 'test-admin-key'
}
if (-not (Test-Path env:PYTHONPATH) -or $env:PYTHONPATH -notlike '*apps/backend*') {
    $env:PYTHONPATH = 'apps/backend'
}

$python = Join-Path (Resolve-Path '.\.venv\Scripts').Path 'python.exe'
if (-not (Test-Path $python)) {
    Write-Error "Python virtual environment not found at .venv."
    exit 1
}

$pytestArgs = @()
if ($Pattern) {
    $pytestArgs += $Pattern
}

& $python -m pytest @pytestArgs
