@echo off
cd /d "%~dp0"
python build_release.py
if errorlevel 1 exit /b 1
echo Paket hazir: dist\OgrenmeMolasi-Windows.zip
