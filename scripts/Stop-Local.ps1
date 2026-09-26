param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'worktrees\backend\backend\.venv\Scripts\python.exe'
$vitePath = Join-Path $projectRoot 'worktrees\frontend\frontend\node_modules\vite\bin\vite.js'

try {
    # Identify this checkout by its executable/script path, never by port alone.
    $snapshot = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $roots = @($snapshot | Where-Object {
        ($_.ExecutablePath -ieq $pythonPath -and
         $_.CommandLine -match '(?:^|\s)-m\s+uvicorn\s+app\.main:app(?:\s|$)') -or
        ($_.Name -ieq 'node.exe' -and
         $_.CommandLine -match ('(?:"|\s)' + [regex]::Escape($vitePath) + '(?:"|\s|$)'))
    })

    if ($roots.Count -eq 0) {
        Write-Host '[OK] No services launched from this project were found.'
    } else {
        $family = [System.Collections.Generic.List[object]]::new()
        $seen = [System.Collections.Generic.HashSet[uint32]]::new()
        foreach ($root in $roots) {
            if ($seen.Add($root.ProcessId)) { $family.Add($root) }
        }
        # Include the Windows venv launcher, Uvicorn reloader, worker and Vite children.
        for ($index = 0; $index -lt $family.Count; $index++) {
            $parent = $family[$index]
            foreach ($child in @($snapshot | Where-Object {
                $_.ParentProcessId -eq $parent.ProcessId -and
                $_.CreationDate -ge $parent.CreationDate
            })) {
                if ($seen.Add($child.ProcessId)) { $family.Add($child) }
            }
        }

        $stopped = 0
        # Stop supervisors before workers so reloaders cannot restart stopped workers.
        foreach ($entry in $family) {
            $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($entry.ProcessId)"
            if (-not $current) { continue }
            # A PID may be reused after the snapshot. Never stop its new owner.
            if ($current.CreationDate -ne $entry.CreationDate -or
                $current.ExecutablePath -ne $entry.ExecutablePath -or
                $current.CommandLine -ne $entry.CommandLine) {
                Write-Host "[NOTE] PID $($entry.ProcessId) changed identity; left untouched."
                continue
            }
            try {
                Stop-Process -Id $entry.ProcessId -Force -ErrorAction Stop
                $stopped++
            } catch {
                $remaining = Get-CimInstance Win32_Process -Filter "ProcessId=$($entry.ProcessId)"
                if ($remaining -and $remaining.CreationDate -eq $entry.CreationDate) { throw }
            }
        }
        Write-Host "[OK] Stopped $stopped project processes."
    }

    foreach ($servicePort in @(8010, 3400)) {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $servicePort -ErrorAction SilentlyContinue)
        if ($listeners.Count -gt 0) {
            Write-Host "[NOTE] Port $servicePort is still occupied. Unidentified services were left untouched."
        } else {
            Write-Host "[OK] Port $servicePort is free."
        }
    }
    Write-Host '[OK] Database, configuration and log files are preserved.'
    exit 0
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
