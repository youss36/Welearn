@echo off
chcp 65001 >nul
echo Verification MySQL...
net start mysql >nul 2>&1
net start MySQL80 >nul 2>&1
REM Petite pause pour laisser MySQL demarrer
timeout /t 2 /nobreak >nul
echo Demarrage Flask...
cd /d "%~dp0"
python app.py
pause
