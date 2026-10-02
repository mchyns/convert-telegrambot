@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0.venv\Scripts\python.exe' -ArgumentList '-m app.main' -WorkingDirectory '%~dp0' -WindowStyle Hidden"
echo ===================================================
echo [OK] DocPDF Bot berhasil dijalankan di background!
echo Bot aktif di Telegram: @mcysconvertbot
echo Jendela ini akan tertutup otomatis...
echo ===================================================
ping 127.0.0.1 -n 2 >nul
exit
