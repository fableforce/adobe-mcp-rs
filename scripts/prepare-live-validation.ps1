param([Parameter(Mandatory=$true)][string]$EvidenceDirectory)
$ErrorActionPreference = 'Stop'
$hostsToTest = @(@('ae','aftereffects',47755), @('pr','premiere',47756),
    @('ps','photoshop',47757), @('ai','illustrator',47758), @('id','indesign',47759))
foreach ($hostInfo in $hostsToTest) {
    $prefix, $hostName, $port = $hostInfo
    $liveRoot = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "$prefix-mcp-bridge"
    $isolatedRoot = Join-Path $EvidenceDirectory "broker-$prefix"
    New-Item -ItemType Directory -Path $isolatedRoot -Force | Out-Null
    $instanceLink = Join-Path $isolatedRoot 'instances'
    if (-not (Test-Path -LiteralPath $instanceLink)) {
        # Only discovery is linked. Registry, configuration, logs and PID files
        # stay isolated. Mailbox paths come from the live bridge's heartbeat.
        New-Item -ItemType Junction -Path $instanceLink -Target (Join-Path $liveRoot 'instances') | Out-Null
    } elseif ((Get-Item -LiteralPath $instanceLink).Target -notcontains (Join-Path $liveRoot 'instances')) {
        throw "Existing instance link has an unexpected destination: $instanceLink"
    }
    $rootToml = $isolatedRoot.Replace('\','/')
    $configPath = Join-Path $EvidenceDirectory "$hostName.toml"
    if (Test-Path -LiteralPath $configPath) { throw "Refusing to overwrite test config: $configPath" }
    @"
host_id = '$hostName'
daemon_addr = '127.0.0.1:$port'
poll_interval_ms = 50
result_timeout_ms = 30000
[bridge]
root_dir = '$rootToml'
command_file = '$rootToml/${prefix}_command.json'
result_file = '$rootToml/${prefix}_mcp_result.json'
"@ | Set-Content -LiteralPath $configPath -Encoding UTF8
    Write-Output $configPath
}
