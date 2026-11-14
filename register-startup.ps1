# Register startup for this Windows user without admin rights.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $root '.venv\Scripts\pythonw.exe'
$script = Join-Path $root 'cleaner.py'
if (-not (Test-Path $pythonw)) { throw 'Run setup-and-login.cmd first.' }
if (-not (Test-Path $script)) { throw 'cleaner.py missing.' }
$shortcutFile = Join-Path ([Environment]::GetFolderPath('Startup')) 'Claude Session Cleaner.lnk'
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = ('"{0}" --loop --min-hours 2 --max-hours 6' -f $script)
$shortcut.WorkingDirectory = $root
$shortcut.Description = 'Random 2-6h Claude Code session cleanup after Windows sign-in'
$shortcut.Save()
Write-Host "Created $shortcutFile"
Write-Host 'This starts at your next Windows sign-in; it does not start immediately.'
