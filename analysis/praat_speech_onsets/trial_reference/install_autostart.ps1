param([switch]$Remove)

$ErrorActionPreference = 'Stop'
$taskName = 'Praat Trial Reference'
$root = $PSScriptRoot
$runner = Join-Path $root 'service_runner.py'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and -not ($existing.Actions.Arguments -contains ('"' + $runner + '"'))) {
    throw "A different task named '$taskName' already exists; it was not changed."
}
if ($Remove) {
    if ($existing) {
        Stop-ScheduledTask -TaskName $taskName
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    Write-Output 'Automatic startup removed. An already running server can remain available until stopped.'
    exit
}

$config = Get-Content -LiteralPath (Join-Path $root 'pipeline_config.json') -Raw | ConvertFrom-Json
$python = Join-Path (Split-Path -Parent $config.viewer_python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Python runtime not found: $python" }
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) { throw "Supervisor not found: $runner" }
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + $runner + '"') -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description 'Keep the local Praat trial reference server available at 127.0.0.1:8765. No browser is launched.'
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
