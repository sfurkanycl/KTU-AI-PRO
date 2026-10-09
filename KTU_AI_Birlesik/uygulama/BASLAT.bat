@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py --no-native-guard
) else (
  py -3.12 main.py --no-native-guard
)
if errorlevel 1 pause
