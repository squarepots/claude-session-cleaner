$ErrorActionPreference = 'Stop'
$shortcutFile = Join-Path ([Environment]::GetFolderPath('Startup')) 'Claude Session Cleaner.lnk'
if (Test-Path $shortcutFile) {
    Remove-Item -LiteralPath $shortcutFile
    Write-Host "Removed $shortcutFile"
} else {
    Write-Host 'No startup shortcut found.'
}
Write-Host 'An already running cleaner process must be stopped separately.'
