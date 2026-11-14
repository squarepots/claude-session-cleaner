# Removes only this cleaner's hook/task, preserving unrelated settings.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\pythonw.exe'
$script = Join-Path $root 'cleaner.py'
$settingsFile = Join-Path $env:USERPROFILE '.claude\settings.json'
if (Test-Path $settingsFile) {
    $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json
    if ($settings.PSObject.Properties['hooks'] -and $settings.hooks.PSObject.Properties['SessionStart']) {
        Copy-Item $settingsFile ($settingsFile + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
        $kept = @()
        foreach ($group in @($settings.hooks.SessionStart)) {
            $handlers = @($group.hooks | Where-Object { !($_.command -eq $python -and @($_.args) -contains $script) })
            if ($handlers.Count -gt 0) { $group.hooks = $handlers; $kept += $group }
        }
        $settings.hooks.SessionStart = @($kept)
        [System.IO.File]::WriteAllText($settingsFile, ($settings | ConvertTo-Json -Depth 80) + "`n", (New-Object System.Text.UTF8Encoding($false)))
    }
}
$task = Get-ScheduledTask -TaskName 'Claude Session Cleaner' -ErrorAction SilentlyContinue
if ($task) { Unregister-ScheduledTask -TaskName 'Claude Session Cleaner' -Confirm:$false }
$legacy = Join-Path ([Environment]::GetFolderPath('Startup')) 'Claude Session Cleaner.lnk'
if (Test-Path $legacy) { Remove-Item $legacy }
Write-Host 'Removed hook and Windows task. Browser profile and logs remain local.'
