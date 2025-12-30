@echo off
setlocal
cd /d "%~dp0"
py -3 launch_app.py
if errorlevel 1 python launch_app.py
pause
