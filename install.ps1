# Устанавливает команду `uniland` без pip (Windows, PowerShell).
# Кладёт uniland.bat в %LOCALAPPDATA%\uniland\bin и добавляет папку в PATH пользователя.
# Запуск:  powershell -ExecutionPolicy Bypass -File install.ps1

$repo = $PSScriptRoot
$bin  = Join-Path $env:LOCALAPPDATA "uniland\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null

# найдём python
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $py) {
    Write-Error "Не найден python. Установи Python 3.10+ и повтори."
    exit 1
}

$bat = @"
@echo off
set PYTHONPATH=$repo;%PYTHONPATH%
"$py" -m uniland %*
"@
Set-Content -Path (Join-Path $bin "uniland.bat") -Value $bat -Encoding ASCII

# добавим папку в PATH пользователя, если её там нет
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
    Write-Host "Папка добавлена в PATH. Открой НОВЫЙ терминал."
}
Write-Host "Готово. Запуск:  uniland run script.uni"
Write-Host "Картинки без установки: png/gif. Для jpg/webp: pip install Pillow (или используй GIF)."
