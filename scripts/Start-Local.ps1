param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'worktrees\backend\backend'
$frontendDir = Join-Path $projectRoot 'worktrees\frontend\frontend'
$pythonPath = Join-Path $backendDir '.venv\Scripts\python.exe'
$vitePath = Join-Path $frontendDir 'node_modules\vite\bin\vite.js'
$logDir = Join-Path $projectRoot '.run-logs'
$backendUrl = 'http://127.0.0.1:8010'
$frontendUrl = 'http://127.0.0.1:3400'

function Test-Backend {
    try {
        $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 2
        $info = Invoke-RestMethod "$backendUrl/" -TimeoutSec 2
        if ($health.status -ne 'ok' -or $info.name -ne 'RivalBull API') { return $false }
        $models = Invoke-RestMethod "$backendUrl/api/models" -TimeoutSec 2
        $schema = Invoke-RestMethod "$backendUrl/openapi.json" -TimeoutSec 2
        return (@($models.options | Where-Object { $_.id -eq 'auto' -and $_.available }).Count -eq 1 -and
                $schema.components.schemas.CreateTaskBody.properties.model.default -eq 'auto')
    } catch { return $false }
}

function Test-Frontend {
    try {
        $page = Invoke-WebRequest "$frontendUrl/" -UseBasicParsing -TimeoutSec 2
        return ($page.StatusCode -eq 200 -and $page.Content -match '<title>RivalBull[^<]*</title>' -and
                $page.Content -match '/@vite/client')
    } catch { return $false }
}

function Assert-PortFree([int]$ServicePort) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $ServicePort -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        throw "Port $ServicePort is occupied by another or unhealthy service. No process was stopped."
    }
}

function Wait-Service([scriptblock]$Check, [string]$Name, [System.Diagnostics.Process]$Process) {
    $deadline = (Get-Date).AddSeconds(40)
    do {
        if (& $Check) { return }
        $Process.Refresh()
        if ($Process.HasExited) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "$Name did not become ready. Check logs in $logDir"
}

try {
    foreach ($required in @($pythonPath, $vitePath, (Join-Path $backendDir '.env'))) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw "Missing required file: $required. See docs\LOCAL_SETUP.md for installation."
        }
    }
    $nodePath = (Get-Command node.exe -ErrorAction Stop).Source
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null

    # Check both ports before starting either service; never kill an occupied port.
    $backendReady = Test-Backend
    $frontendReady = Test-Frontend
    if (-not $backendReady) { Assert-PortFree 8010 }
    if (-not $frontendReady) { Assert-PortFree 3400 }

    if ($backendReady) {
        Write-Host '[OK] Backend is already running.'
    } else {
        Write-Host '[1/2] Starting backend...'
        $backendProcess = Start-Process -FilePath $pythonPath -WorkingDirectory $backendDir `
            -ArgumentList @('-X', 'utf8', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                            '--port', '8010', '--reload', '--reload-include', '.env') `
            -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $logDir 'backend.stdout.log') `
            -RedirectStandardError (Join-Path $logDir 'backend.stderr.log')
        Wait-Service { Test-Backend } 'Backend' $backendProcess
    }

    if ($frontendReady) {
        Write-Host '[OK] Frontend is already running.'
    } else {
        Write-Host '[2/2] Starting frontend...'
        # Start-Process joins ArgumentList into one string: quote the Vite path explicitly.
        $frontendProcess = Start-Process -FilePath $nodePath -WorkingDirectory $frontendDir `
            -ArgumentList @(('"{0}"' -f $vitePath), '--host', '127.0.0.1') `
            -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $logDir 'frontend.stdout.log') `
            -RedirectStandardError (Join-Path $logDir 'frontend.stderr.log')
        Wait-Service { Test-Frontend } 'Frontend' $frontendProcess
    }

    # Verify the frontend proxy reaches this API, without consuming model/search quota.
    $proxyHealth = Invoke-RestMethod "$frontendUrl/api/experts" -TimeoutSec 5
    if (@($proxyHealth).Count -eq 0) { throw 'Frontend API proxy returned no experts.' }
    $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 5
    if (-not $health.llm_configured) {
        Write-Host '[NOTE] Fill LLM_API_KEY in worktrees\backend\backend\.env to enable research.'
    }

    Write-Host "[OK] App: $frontendUrl"
    Write-Host "[OK] API: $backendUrl"
    Write-Host "Logs: $logDir"
    if (-not $NoBrowser) { Start-Process $frontendUrl }
    exit 0
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
