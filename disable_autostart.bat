@echo off
title Nonaktifkan Auto-Start DocPDF Bot
echo ===================================================
echo Menonaktifkan Auto-Start DocPDF Bot...
echo ===================================================

powershell -NoProfile -Command ^
    "$startupFolder = [System.Environment]::GetFolderPath('Startup'); " ^
    "$shortcutPath = Join-Path $startupFolder 'DocPDF_Bot.lnk'; " ^
    "if (Test-Path $shortcutPath) { " ^
    "   Remove-Item $shortcutPath -Force; " ^
    "   Write-Host '✅ Auto-Start BERHASIL dinonaktifkan.' -ForegroundColor Green; " ^
    "} else { " ^
    "   Write-Host 'ℹ️ Auto-Start sebelumnya belum diaktifkan.' -ForegroundColor Yellow; " ^
    "}"

echo.
pause
