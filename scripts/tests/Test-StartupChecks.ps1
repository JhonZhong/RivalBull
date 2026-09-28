$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot '..\Start-Local.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path $scriptPath).Path, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Startup script has syntax errors.' }
# Load only the readiness functions; never execute the launcher in a test.
$ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -in @('Test-Backend', 'Test-Frontend')
}, $true) | ForEach-Object { Invoke-Expression $_.Extent.Text }
$backendUrl = 'http://backend.test'
$frontendUrl = 'http://frontend.test'
$script:apiName = 'RivalBull API'
$script:hasCatalog = $true
$script:hasModel = $true
$script:title = 'RivalBull'
function Invoke-RestMethod($Uri, $TimeoutSec) {
    switch -Wildcard ($Uri) {
        '*/health' { return @{ status = 'ok' } }
        '*/api/models' {
            if (-not $script:hasCatalog) { throw 'No catalog' }
            return @{ options = @(@{ id = 'auto'; available = $true }) }
        }
        '*/openapi.json' {
            $properties = @{}
            if ($script:hasModel) { $properties.model = @{ default = 'auto' } }
            return @{ components = @{ schemas = @{ CreateTaskBody = @{ properties = $properties } } } }
        }
        default { return @{ name = $script:apiName } }
    }
}
function Invoke-WebRequest($Uri, [switch]$UseBasicParsing, $TimeoutSec) {
    return @{ StatusCode = 200; Content = "<title>$script:title</title><script src='/@vite/client'></script>" }
}
if (-not (Test-Backend)) { throw 'Current backend rejected' }
$script:apiName = 'Verda API'
if (Test-Backend) { throw 'Legacy backend accepted' }
$script:apiName = 'RivalBull API'
$script:hasCatalog = $false
if (Test-Backend) { throw 'Missing catalog accepted' }
$script:hasCatalog = $true
$script:hasModel = $false
if (Test-Backend) { throw 'Missing model schema accepted' }
if (-not (Test-Frontend)) { throw 'Current frontend rejected' }
$script:title = 'Verda'
if (Test-Frontend) { throw 'Legacy frontend accepted' }
Write-Output '6 startup readiness checks passed.'
