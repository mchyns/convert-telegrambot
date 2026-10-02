@echo off
title Status DocPDF Bot
echo ===================================================
echo Memeriksa status DocPDF Bot di background...
echo ===================================================

powershell -NoProfile -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.main*' }; " ^
    "if ($procs) { " ^
    "   Write-Host '✅ DocPDF Bot SEDANG AKTIF di background!' -ForegroundColor Green; " ^
    "   $procs | ForEach-Object { Write-Host ('   • Process ID (PID) : ' + $_.ProcessId) -ForegroundColor Cyan }; " ^
    "} else { " ^
    "   Write-Host '❌ DocPDF Bot SEDANG MATI / TIDAK BERJALAN.' -ForegroundColor Red; " ^
    "   Write-Host '   Untuk menyalakan, klik dua kali file start_bot.vbs' -ForegroundColor Yellow; " ^
    "}"

echo.
pause
