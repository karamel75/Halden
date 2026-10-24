@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installation des dependances...
python -m pip install -q -r requirements.txt
python -m halden demo
echo.
echo Ouverture de la console Halden (Ctrl+C pour arreter)...
python -m halden console
pause
