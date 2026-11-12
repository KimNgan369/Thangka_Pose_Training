@echo off
cd /d "%~dp0"
py -3.10 local_app.py %*
if errorlevel 1 pause
