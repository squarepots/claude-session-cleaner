# Run after setup-and-login.cmd. Adds a user-level Claude Code hook and Windows task.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\pythonw.exe'
$script = Join-Path $root 'cleaner.py'
if (!(Test-Path $python) -or !(Test-Path $script)) { throw 'Run setup-and-login.cmd first.' }

$settingsFile = Join-Path $env:USERPROFILE '.claude\settings.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $settingsFile) -Force | Out-Null
if (Test-Path $settingsFile) {
    Copy-Item $settingsFile ($settingsFile + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json
} else { $settings = [pscustomobject]@{} }
if (!$settings.PSObject.Properties['hooks']) {
    $settings | Add-Member -NotePropertyName 'hooks' -NotePropertyValue ([pscustomobject]@{})
}
$hook = [pscustomobject]@{
    matcher = 'startup|resume'
    hooks = @([pscustomobject]@{
        type = 'command'
        command = $python
        args = @($script, '--check')
        async = $true
    })
}
$old = @()
if ($settings.hooks.PSObject.Properties['SessionStart']) {
    foreach ($group in @($settings.hooks.SessionStart)) {
        $keep = @($group.hooks | Where-Object { !($_.command -eq $python -and @($_.args) -contains $script) })
        if ($keep.Count -gt 0) { $group.hooks = $keep; $old += $group }
    }
    $settings.hooks.SessionStart = @($old) + @($hook)
} else {
    $settings.hooks | Add-Member -NotePropertyName 'SessionStart' -NotePropertyValue @($hook)
}
$json = $settings | ConvertTo-Json -Depth 80
[System.IO.File]::WriteAllText($settingsFile, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))

$taskName = 'Claude Session Cleaner'
$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $python -Argument ('"{0}" --check' -f $script) -WorkingDirectory $root
$atLogin = New-ScheduledTaskTrigger -AtLogOn -User $account
$periodic = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$options = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($atLogin, $periodic) -Settings $options -Principal $principal -Description 'Checks saved random deadline; deletes Anthropic-stored sessions only when due' -Force | Out-Null
$legacy = Join-Path ([Environment]::GetFolderPath('Startup')) 'Claude Session Cleaner.lnk'
if (Test-Path $legacy) { Remove-Item $legacy }
Write-Host 'Installed SessionStart hook and Windows scheduled task. Test --once first.'
