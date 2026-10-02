@echo off
title Hentikan DocPDF Bot
echo ===================================================
echo Menghentikan DocPDF Bot yang berjalan di background...
echo ===================================================

powershell -NoProfile -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.main*' }; " ^
    "if ($procs) { " ^
    "   $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('[OK] Bot dengan PID ' + $_.ProcessId + ' berhasil dihentikan.') -ForegroundColor Green }; " ^
    "} else { " ^
    "   Write-Host '[INFO] Tidak ada proses DocPDF Bot yang sedang berjalan.' -ForegroundColor Yellow; " ^
    "}"

echo.
pause
