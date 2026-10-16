param(
    [Parameter(Mandatory = $true)][string]$ClientJson,
    [Parameter(Mandatory = $true)][string]$AdminEmails,
    [switch]$Directory,
    [switch]$OfficialMode
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$clientPath = (Resolve-Path -LiteralPath $ClientJson).Path
$oauthConfig = Get-Content -LiteralPath $clientPath -Raw | ConvertFrom-Json
$oauthWeb = $oauthConfig.web
if (-not $oauthWeb.client_id -or -not $oauthWeb.client_secret) { throw 'Choose the downloaded JSON for a Web application OAuth client.' }
if ($oauthWeb.redirect_uris -notcontains 'http://127.0.0.1:8765/auth/callback') { throw 'Add http://127.0.0.1:8765/auth/callback to the client redirect URIs and download the JSON again.' }
$adminList = @($AdminEmails.Split(',') | ForEach-Object { $_.Trim().ToLowerInvariant() })
if ($adminList.Count -eq 0 -or @($adminList | Where-Object { $_ -notmatch '^[A-Za-z0-9.!#$%&''*+/=?^_`{|}~-]+@qiu\.edu\.my$' }).Count -gt 0) { throw 'Use actual @qiu.edu.my SLD administrator email addresses.' }
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) { $runtimePython = (Get-Command python -ErrorAction Stop).Source }
$environmentKeys = @('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_DIRECTORY_ENABLED','SLD_ADMIN_EMAILS','SLD_APP_URL')
$previousEnvironment = @{}
foreach ($key in $environmentKeys) { $previousEnvironment[$key] = [Environment]::GetEnvironmentVariable($key,'Process') }
try {
    $env:GOOGLE_CLIENT_ID = $oauthWeb.client_id
    $env:GOOGLE_CLIENT_SECRET = $oauthWeb.client_secret
    $env:GOOGLE_DIRECTORY_ENABLED = if ($Directory) { 'true' } else { 'false' }
    $env:SLD_ADMIN_EMAILS = $adminList -join ','
    $env:SLD_APP_URL = 'http://127.0.0.1:8765'
    $serverArgs = @((Join-Path $projectRoot 'server.py'),'--port','8765')
    if (-not $OfficialMode) { $serverArgs += '--preview' }
    Write-Host 'Starting QIU SLD on http://127.0.0.1:8765. Credentials stay in this process.'
    & $runtimePython @serverArgs
    if ($LASTEXITCODE -ne 0) { throw 'The server could not start. Check its message above and whether another server occupies port 8765.' }
}
finally {
    foreach ($key in $environmentKeys) { [Environment]::SetEnvironmentVariable($key,$previousEnvironment[$key],'Process') }
    $oauthConfig = $null
    $oauthWeb = $null
}
