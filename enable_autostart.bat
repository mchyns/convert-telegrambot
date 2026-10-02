@echo off
title Aktifkan Auto-Start DocPDF Bot
echo ===================================================
echo Mengaktifkan Auto-Start saat Windows menyala...
echo ===================================================

powershell -NoProfile -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$startupFolder = [System.Environment]::GetFolderPath('Startup'); " ^
    "$shortcutPath = Join-Path $startupFolder 'DocPDF_Bot.lnk'; " ^
    "$targetScript = Join-Path (Get-Location) 'start_bot.bat'; " ^
    "$shortcut = $wsh.CreateShortcut($shortcutPath); " ^
    "$shortcut.TargetPath = $targetScript; " ^
    "$shortcut.WorkingDirectory = (Get-Location).Path; " ^
    "$shortcut.WindowStyle = 7; " ^
    "$shortcut.Description = 'Telegram DocPDF Bot Autostart'; " ^
    "$shortcut.Save(); " ^
    "Write-Host '✅ Auto-Start BERHASIL diaktifkan!' -ForegroundColor Green; " ^
    "Write-Host ('   File shortcut dibuat di: ' + $shortcutPath) -ForegroundColor Gray; " ^
    "Write-Host '   Mulai sekarang, bot akan otomatis jalan setiap laptop dinyalakan.' -ForegroundColor Cyan;"

echo.
pause
